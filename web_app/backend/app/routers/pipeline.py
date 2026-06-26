import csv
import io
import json
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["pipeline"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECT_ROOT = BASE_DIR.parent.parent

_runs: dict[str, dict] = {}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _read_log_lines(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                stage = obj.get("stage", "?")
                file = obj.get("file", "?")
                status = obj.get("status", "?")
                lines.append(f"[{stage}] {file} — {status}")
            except json.JSONDecodeError:
                lines.append(line)
    return lines


def _read_log_objects(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    objects = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                objects.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return objects


def _get_file_basenames(log_entries: list[dict]) -> list[str]:
    basenames = []
    seen = set()
    for entry in log_entries:
        if entry.get("stage") == "normalize":
            fname = entry.get("file", "")
            if fname and fname not in seen:
                seen.add(fname)
                basenames.append(fname)
    return basenames


def _per_file_stages(log_entries: list[dict], basename: str) -> dict[str, str]:
    stages = {"normalize": "pending", "segment": "pending", "classify": "pending"}
    prefix = basename + "_"
    for entry in log_entries:
        stage = entry.get("stage", "")
        file_field = entry.get("file", "")
        status = entry.get("status", "")
        if stage == "normalize" and file_field == basename:
            stages["normalize"] = "done" if status == "ok" else "failed"
        elif stage == "segment" and file_field == basename:
            stages["segment"] = "done" if status == "ok" else "failed"
        elif stage == "classify" and file_field.startswith(prefix):
            if status in ("keep", "reject"):
                stages["classify"] = "done"
            elif status == "fail":
                stages["classify"] = "failed"
    return stages


def _build_run_response(run_id: str, run_info: dict) -> dict:
    output_dir = run_info["output_dir"]
    manifest_rows = _read_csv(output_dir / "manifest.csv")
    rejected_rows = _read_csv(output_dir / "rejected.csv")
    log_lines = _read_log_lines(output_dir / "pipeline.log")
    log_entries = _read_log_objects(output_dir / "pipeline.log")

    status = run_info["status"]
    file_names: list[str] = run_info.get("file_names", [])
    source_names: list[str] = run_info.get("source_names", [])
    source_type = run_info.get("source_type", "manual")
    dialect = run_info.get("dialect", "")
    start_time = run_info.get("start_time", 0)

    if status == "queued":
        pipeline_status = "queued"
    elif status == "running":
        pipeline_status = "running"
    elif status == "done":
        pipeline_status = "done"
    else:
        pipeline_status = "failed"

    basenames = _get_file_basenames(log_entries)
    if not basenames:
        basenames = [Path(f).stem for f in file_names]
    if not basenames:
        basenames = [Path(f).stem for f in file_names]

    files = []
    for i, basename in enumerate(basenames):
        original_filename = ""
        for fname in file_names:
            if Path(fname).stem == basename:
                original_filename = fname
                break
        if not original_filename:
            original_filename = basename

        per_source_name = source_names[i] if i < len(source_names) else basename
        per_source_type = source_type if isinstance(source_type, str) else (source_type[i] if isinstance(source_type, list) and i < len(source_type) else "manual")

        stage_statuses = _per_file_stages(log_entries, basename)
        normalize_status = stage_statuses.get("normalize", "pending")
        segment_status = stage_statuses.get("segment", "pending")
        classify_status = stage_statuses.get("classify", "pending")

        if pipeline_status == "queued":
            normalize_status = segment_status = classify_status = "pending"
        elif pipeline_status == "done":
            all_done = all(s == "done" for s in (normalize_status, segment_status, classify_status))
            if not all_done:
                normalize_status = segment_status = classify_status = "done"

        file_segments = []
        for row in manifest_rows:
            if row.get("source_name", "") == per_source_name:
                file_segments.append({
                    "label": f"{row.get('predicted_lang', '?')} {float(row.get('predicted_score', 0)):.3f}s",
                    "status": "kept",
                    "duration_s": round(int(row.get('duration_ms', 0)) / 1000, 1),
                })
        for row in rejected_rows:
            if row.get("source_name", "") == per_source_name:
                file_segments.append({
                    "label": f"{row.get('predicted_lang', '?')} {float(row.get('predicted_score', 0)):.3f}s",
                    "status": "rejected",
                    "duration_s": round(int(row.get('duration_ms', 0)) / 1000, 1),
                })

        if status in ("done", "failed"):
            result_status = status
        elif status == "running":
            result_status = "running"
        else:
            result_status = "pending"

        files.append({
            "file_name": original_filename,
            "source_name": per_source_name,
            "source_type": per_source_type,
            "label_dialect": dialect,
            "stages": [
                {"name": "normalize", "status": normalize_status},
                {"name": "segment", "status": segment_status},
                {"name": "classify", "status": classify_status},
            ],
            "segments": file_segments,
            "result": result_status,
        })

    kept = len(manifest_rows)
    rejected = len(rejected_rows)
    total_ms = sum(int(r.get('duration_ms', 0)) for r in manifest_rows) + sum(int(r.get('duration_ms', 0)) for r in rejected_rows)

    rejection_reasons = {}
    for r in rejected_rows:
        reason = r.get('reject_reason', 'unknown')
        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    return {
        "run_id": run_id,
        "status": pipeline_status,
        "files": files,
        "summary": {
            "normalization": "successful" if pipeline_status == "done" else ("failed" if pipeline_status == "failed" else "pending"),
            "segment_files": len(basenames),
            "segment_count": kept + rejected,
            "segment_duration_s": round(total_ms / 1000, 1),
            "classify_retained": kept,
            "classify_rejected": rejected,
            "rejection_reasons": rejection_reasons,
            "dialect": dialect,
            "run_time_s": run_info.get("run_time_s", round(time.time() - start_time, 1) if start_time else 0),
        },
        "output_log": log_lines,
        "output_paths": {
            "audio_dir": f"data/output/{run_id}/audio/",
            "rejected_dir": f"data/output/{run_id}/rejected/",
            "manifest_csv": f"data/output/{run_id}/manifest.csv",
            "rejected_csv": f"data/output/{run_id}/rejected.csv",
            "pipeline_log": f"data/output/{run_id}/pipeline.log",
        },
    }


@router.post("/api/pipeline/run")
async def run_pipeline(
    files: list[UploadFile] = File(...),
    source_name: str = Form(""),
    source_type: str = Form(""),
    dialect: str = Form(""),
):
    run_id = str(uuid.uuid4())
    input_dir = Path(f"/tmp/pipeline_input_{run_id}")
    output_dir = DATA_DIR / "output" / run_id

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_names = []
    source_names = []
    yml_entries = []

    for i, file in enumerate(files):
        original_filename = file.filename or f"{run_id}_{i}.wav"
        file_path = input_dir / original_filename
        content = await file.read()
        file_path.write_bytes(content)
        file_names.append(original_filename)

        per_source_name = f"{run_id}_{i}"
        source_names.append(per_source_name)

        yml_entries.append({
            "path": original_filename,
            "dialect_label": dialect,
            "source_name": per_source_name,
            "source_type": source_type or "manual",
        })

    lines = ["defaults:", "  confidence: high", "files:"]
    for e in yml_entries:
        lines.append(f"  - path: {e['path']}")
        lines.append(f"    dialect_label: {e['dialect_label']}")
        lines.append(f"    source_name: {e['source_name']}")
        lines.append(f"    source_type: {e['source_type']}")
    (input_dir / "manifest.yml").write_text("\n".join(lines) + "\n")

    start = time.time()
    _runs[run_id] = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "start_time": start,
        "status": "queued",
        "process": None,
        "run_time_s": 0,
        "file_names": file_names,
        "source_names": source_names,
        "source_type": source_type or "manual",
        "dialect": dialect,
    }

    def _run():
        _runs[run_id]["status"] = "running"
        proc = subprocess.Popen(
            ["python3", "-m", "pipeline.run", str(input_dir), str(output_dir)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _runs[run_id]["process"] = proc
        proc.wait()
        _runs[run_id]["run_time_s"] = round(time.time() - start, 1)
        _runs[run_id]["status"] = "done" if proc.returncode == 0 else "failed"
        shutil.rmtree(input_dir, ignore_errors=True)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"run_id": run_id, "status": "queued"}


@router.get("/api/pipeline/runs")
async def list_pipeline_runs():
    runs = []
    seen = set()

    for run_id, run_info in _runs.items():
        seen.add(run_id)
        runs.append({"run_id": run_id, "status": run_info["status"]})

    output_dir = DATA_DIR / "output"
    if output_dir.exists():
        for run_dir in sorted(output_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            rid = run_dir.name
            if rid in seen:
                continue
            seen.add(rid)
            status = "done" if (run_dir / "manifest.csv").exists() else "running"
            runs.append({"run_id": rid, "status": status})

    return {"runs": runs}


@router.get("/api/pipeline/{run_id}")
async def get_pipeline_run(run_id: str):
    run_info = _runs.get(run_id)

    if run_info is None:
        output_dir = DATA_DIR / "output" / run_id
        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        run_info = {
            "output_dir": output_dir,
            "status": "done",
            "file_names": [],
            "source_names": [],
            "source_type": "",
            "dialect": "",
            "start_time": 0,
            "run_time_s": 0,
        }

    return _build_run_response(run_id, run_info)


@router.get("/api/pipeline/{run_id}/download")
async def download_pipeline_output(run_id: str):
    output_dir = DATA_DIR / "output" / run_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in output_dir.rglob("*"):
            if path.is_file():
                arcname = str(path.relative_to(output_dir))
                zf.write(path, arcname)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="pipeline_{run_id}.zip"'},
    )
