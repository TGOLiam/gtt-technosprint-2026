from fastapi import APIRouter, Query

from app.db import get_db

router = APIRouter(tags=["prompts"])


@router.get("/api/prompt")
async def get_prompt(dialect: str = Query("", description="Filter by dialect variant")):
    db = get_db()

    if dialect:
        rows = db.execute(
            "SELECT id, text, dialect_variant, category, times_recorded "
            "FROM prompts WHERE dialect_variant = ? "
            "ORDER BY times_recorded ASC, RANDOM() LIMIT 1",
            (dialect,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, text, dialect_variant, category, times_recorded "
            "FROM prompts ORDER BY times_recorded ASC, RANDOM() LIMIT 1",
        ).fetchall()

    if not rows:
        rows = db.execute(
            "SELECT id, text, dialect_variant, category, times_recorded "
            "FROM prompts ORDER BY times_recorded ASC, RANDOM() LIMIT 1",
        ).fetchall()

    db.close()

    if not rows:
        return {"id": "", "text": "Magayon an panahon ngunyan.", "dialect_variant": "", "category": "fallback"}

    row = rows[0]
    return {
        "id": row["id"],
        "text": row["text"],
        "dialect_variant": row["dialect_variant"],
        "category": row["category"],
    }
