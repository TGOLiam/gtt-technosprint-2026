from fastapi import APIRouter
from app.db import get_db
from contextlib import closing

router = APIRouter(tags=["stats"])


@router.get("/api/stats")
async def get_stats():
    with closing(get_db()) as db:
        # Combine dialect counts into one query
        dialect_rows = db.execute(
            "SELECT s.dialect_label, COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id GROUP BY s.dialect_label"
        ).fetchall()
        dialect_counts = dict(dialect_rows)

        # Combine total recordings, speakers, and duration into one query
        row = db.execute(
            "SELECT COUNT(*), COUNT(DISTINCT speaker_id), COALESCE(SUM(duration_ms), 0) FROM recordings"
        ).fetchone()
        total, speakers, total_ms = row

        # Combine prompt counts into one query
        prompt_row = db.execute(
            "SELECT COUNT(*), SUM(times_recorded > 0) FROM prompts"
        ).fetchone()
        prompts_total, prompts_covered = prompt_row

    return {
        "total_recordings": total,
        "naga_count": dialect_counts.get("naga", 0),
        "albay_count": dialect_counts.get("albay", 0),
        "total_speakers": speakers,
        "total_duration_minutes": round(total_ms / 60000, 1),
        "prompts_covered": prompts_covered or 0,
        "prompts_total": prompts_total,
    }
