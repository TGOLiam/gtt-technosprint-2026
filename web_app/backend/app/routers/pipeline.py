import csv
import subprocess
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["pipeline"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECT_ROOT = BASE_DIR.parent.parent


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _compute_summary(manifest_rows: list[dict], rejected_rows: list[dict]) -> dict:
    kept = len(manifest_rows)
    rejected = len(rejected_rows)

    languages: dict[str, int] = {}
    dialect_labels: dict[str, int] = {}
    total_duration_ms = 0

    for row in manifest_rows:
        lang = row.get("predicted_lang", "unknown")
        languages[lang] = languages.get(lang, 0) + 1

        label = row.get("dialect_label", "unknown")
        dialect_labels[label] = dialect_labels.get(label, 0) + 1

        try:
            total_duration_ms += int(row.get("duration_ms", 0))
        except (ValueError, TypeError):
            pass

    reject_reasons: dict[str, int] = {}
    for row in rejected_rows:
        reason = row.get("reject_reason", "unknown")
        reject_reasons[reason] = reject_reasons.get(reason, 0) + 1

    return {
        "kept": kept,
        "rejected": rejected,
        "languages": languages,
        "reject_reasons": reject_reasons,
        "dialect_labels": dialect_labels,
        "total_duration_ms": total_duration_ms,
    }


@router.post("/api/pipeline/run")
async def run_pipeline():
    run_id = str(uuid.uuid4())
    input_dir = DATA_DIR / "input"
    output_dir = DATA_DIR / "output" / run_id

    if not input_dir.exists():
        raise HTTPException(status_code=400, detail="Input directory not found")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["python3", "-m", "pipeline.run", str(input_dir), str(output_dir)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            return {"run_id": run_id, "status": "completed"}
        return {"run_id": run_id, "status": "failed", "error": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"run_id": run_id, "status": "running"}
    except Exception as e:
        return {"run_id": run_id, "status": "failed", "error": str(e)}


@router.get("/api/pipeline/runs")
async def list_pipeline_runs():
    output_dir = DATA_DIR / "output"
    if not output_dir.exists():
        return {"runs": []}

    runs = []
    for run_dir in sorted(output_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue

        manifest_rows = _read_csv(run_dir / "manifest.csv")
        rejected_rows = _read_csv(run_dir / "rejected.csv")

        status = "completed" if manifest_rows else "running"
        summary = _compute_summary(manifest_rows, rejected_rows)

        runs.append({
            "run_id": run_dir.name,
            "status": status,
            "summary": summary,
        })

    return {"runs": runs}


@router.get("/api/pipeline/{run_id}")
async def get_pipeline_run(run_id: str):
    output_dir = DATA_DIR / "output" / run_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")

    manifest_rows = _read_csv(output_dir / "manifest.csv")
    rejected_rows = _read_csv(output_dir / "rejected.csv")
    summary = _compute_summary(manifest_rows, rejected_rows)

    return {
        "run_id": run_id,
        "manifest": manifest_rows,
        "rejected": rejected_rows,
        "summary": summary,
    }
