import csv
from contextlib import closing
from pathlib import Path
from fastapi import APIRouter

from app.db import get_db

router = APIRouter(tags=["stats"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


@router.get("/api/stats")
async def get_stats(include_pipeline: bool = False):
    with closing(get_db()) as db:
        dialect_rows = db.execute(
            "SELECT s.dialect_label, COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id GROUP BY s.dialect_label"
        ).fetchall()
        dialect_counts = dict(dialect_rows)

        row = db.execute(
            "SELECT COUNT(*), COUNT(DISTINCT speaker_id), COALESCE(SUM(duration_ms), 0) FROM recordings"
        ).fetchone()
        total, speakers, total_ms = row

        prompt_row = db.execute(
            "SELECT COUNT(*), SUM(times_recorded > 0) FROM prompts"
        ).fetchone()
        prompts_total, prompts_covered = prompt_row

    result = {
        "total_recordings": total,
        "naga_count": dialect_counts.get("naga", 0),
        "albay_count": dialect_counts.get("albay", 0),
        "total_speakers": speakers,
        "total_duration_minutes": round(total_ms / 60000, 1),
        "prompts_covered": prompts_covered or 0,
        "prompts_total": prompts_total,
    }

    if include_pipeline:
        output_dir = DATA_DIR / "output"
        if output_dir.exists():
            run_dirs = [
                d for d in output_dir.iterdir() if d.is_dir()
            ]
            if run_dirs:
                latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
                manifest_rows = _read_csv(latest / "manifest.csv")
                rejected_rows = _read_csv(latest / "rejected.csv")
                result["pipeline"] = _compute_summary(manifest_rows, rejected_rows)

    return result


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
