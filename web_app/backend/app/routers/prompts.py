from fastapi import APIRouter, Query
from app.db import get_db
from contextlib import closing

router = APIRouter(tags=["prompts"])

@router.get("/api/prompt")
async def get_prompt(dialect: str = Query("", description="Filter by dialect variant")):
    with closing(get_db()) as db:
        if dialect:
            row = db.execute(
                "SELECT id, text, dialect_variant, category FROM prompts "
                "WHERE dialect_variant = ? ORDER BY times_recorded ASC, RANDOM() LIMIT 1",
                (dialect,),
            ).fetchone()
        else:
            row = None

        # Actual fallback — any dialect
        if not row:
            row = db.execute(
                "SELECT id, text, dialect_variant, category FROM prompts "
                "ORDER BY times_recorded ASC, RANDOM() LIMIT 1",
            ).fetchone()

        if not row:
            return {"id": "", "text": "Magayon an panahon ngunyan.", "dialect_variant": "", "category": "fallback"}

        return {
            "id": row["id"],
            "text": row["text"],
            "dialect_variant": row["dialect_variant"],
            "category": row["category"],
        }
