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


def _read_log(path: Path) -> list[str]:
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


def _parse_log_stages(log_lines: list[str]) -> dict[str, str]:
    stages = {"normalize": "pending", "segment": "pending", "classify": "pending"}
    for line in log_lines:
        for stage in ("normalize", "segment", "classify"):
            if f"[{stage}]" in line:
                stages[stage] = "running"
                if "ok" in line or "keep" in line or "reject" in line:
                    stages[stage] = "done"
                if "fail" in line:
                    stages[stage] = "failed"
    return stages


def _build_run_response(run_id: str, run_info: dict) -> dict:
    output_dir = run_info["output_dir"]
    manifest_rows = _read_csv(output_dir / "manifest.csv")
    rejected_rows = _read_csv(output_dir / "rejected.csv")
    log_lines = _read_log(output_dir / "pipeline.log")

    status = run_info["status"]
    file_name = run_info.get("file_name", "")
    dialect = run_info.get("dialect", "")
    source_name = run_info.get("source_name", "")
    source_type = run_info.get("source_type", "")
    start_time = run_info.get("start_time", 0)

    log_stages = _parse_log_stages(log_lines)
    normalize_status = log_stages.get("normalize", "pending")
    segment_status = log_stages.get("segment", "pending")
    classify_status = log_stages.get("classify", "pending")

    if status == "queued":
        normalize_status = segment_status = classify_status = "pending"
    elif status == "done":
        if all(s == "done" for s in (normalize_status, segment_status, classify_status)):
            pass
        else:
            normalize_status = segment_status = classify_status = "done"

    segments = []
    for row in manifest_rows:
        segments.append({
            "label": f"{row.get('predicted_lang', '?')} {float(row.get('predicted_score', 0)):.3f}s",
            "status": "kept",
            "duration_s": round(int(row.get('duration_ms', 0)) / 1000, 1),
        })
    for row in rejected_rows:
        segments.append({
            "label": f"{row.get('predicted_lang', '?')} {float(row.get('predicted_score', 0)):.3f}s",
            "status": "rejected",
            "duration_s": round(int(row.get('duration_ms', 0)) / 1000, 1),
        })

    kept = len(manifest_rows)
    rejected = len(rejected_rows)
    total_ms = sum(int(r.get('duration_ms', 0)) for r in manifest_rows) + sum(int(r.get('duration_ms', 0)) for r in rejected_rows)

    rejection_reasons = {}
    for r in rejected_rows:
        reason = r.get('reject_reason', 'unknown')
        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

    if status == "done":
        pipeline_status = "done"
    elif status == "running":
        pipeline_status = "running"
    elif status == "queued":
        pipeline_status = "queued"
    else:
        pipeline_status = "failed"

    if status in ("done", "failed"):
        result_status = status
    elif status == "running":
        result_status = "running"
    else:
        result_status = "pending"

    return {
        "run_id": run_id,
        "status": pipeline_status,
        "file": {
            "file_name": file_name,
            "source_name": source_name,
            "source_type": source_type,
            "label_dialect": dialect,
            "stages": [
                {"name": "normalize", "status": normalize_status},
                {"name": "segment", "status": segment_status},
                {"name": "classify", "status": classify_status},
            ],
            "segments": segments,
            "result": result_status,
        },
        "summary": {
            "normalization": "successful" if normalize_status == "done" else ("failed" if normalize_status == "failed" else "pending"),
            "segment_files": 1,
            "segment_count": len(segments),
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
    file: UploadFile = File(...),
    source_name: str = Form(""),
    source_type: str = Form(""),
    dialect: str = Form(""),
):
    run_id = str(uuid.uuid4())
    input_dir = Path(f"/tmp/pipeline_input_{run_id}")
    output_dir = DATA_DIR / "output" / run_id

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename or f"{run_id}.wav"
    file_path = input_dir / original_filename
    content = await file.read()
    file_path.write_bytes(content)

    manifest_yml = f"""defaults:
  confidence: high
files:
  - path: {original_filename}
    dialect_label: {dialect}
    source_name: {source_name or run_id}
    source_type: {source_type or "manual"}
"""
    (input_dir / "manifest.yml").write_text(manifest_yml)

    start = time.time()
    _runs[run_id] = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "start_time": start,
        "status": "queued",
        "process": None,
        "run_time_s": 0,
        "file_name": original_filename,
        "dialect": dialect,
        "source_name": source_name,
        "source_type": source_type,
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
            "file_name": "",
            "dialect": "",
            "source_name": "",
            "source_type": "",
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
