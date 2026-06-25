from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.dictionary_service import DATASET, search_dataset

router = APIRouter(prefix="/api", tags=["dictionary"])


class WordEntry(BaseModel):
    word: str
    gloss: str
    dialect: str
    source: str


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[WordEntry]


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query("", description="Bikol word or English gloss to search for")):
    """
    Called by the frontend like:
        GET /api/search?q=tubig

    Matches against both the Bikol word and its English gloss, so the
    same box works whether the user types Bikol or English.
    """
    results = search_dataset(q)
    return SearchResponse(query=q, count=len(results), results=results)


@router.get("/health")
def health():
    """Quick check that the API is up and the dataset loaded correctly."""
    return {"status": "ok", "entries_loaded": len(DATASET)}
