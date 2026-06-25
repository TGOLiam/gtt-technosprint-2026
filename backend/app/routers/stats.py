from fastapi import APIRouter

from app.db import get_db

router = APIRouter(tags=["stats"])


@router.get("/api/stats")
async def get_stats():
    db = get_db()

    total = db.execute("SELECT COUNT(*) FROM recordings").fetchone()[0]

    naga = db.execute(
        "SELECT COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id WHERE s.dialect_label = 'naga'"
    ).fetchone()[0]

    albay = db.execute(
        "SELECT COUNT(*) FROM recordings r JOIN speakers s ON r.speaker_id = s.id WHERE s.dialect_label = 'albay'"
    ).fetchone()[0]

    speakers = db.execute("SELECT COUNT(DISTINCT id) FROM speakers").fetchone()[0]

    total_ms = db.execute("SELECT COALESCE(SUM(duration_ms), 0) FROM recordings").fetchone()[0]

    prompts_covered = db.execute("SELECT COUNT(*) FROM prompts WHERE times_recorded > 0").fetchone()[0]
    prompts_total = db.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]

    db.close()

    return {
        "total_recordings": total,
        "naga_count": naga,
        "albay_count": albay,
        "total_speakers": speakers,
        "total_duration_minutes": round(total_ms / 60000, 1),
        "prompts_covered": prompts_covered,
        "prompts_total": prompts_total,
    }
