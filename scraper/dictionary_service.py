"""
Loads the Bikol word dataset (JSONL) into memory once at import time,
and exposes a search function the router calls per-request.

Keeping this separate from the router means the search logic can be
unit-tested or reused (e.g. by a future CLI script) without needing
a running FastAPI app.
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "bikol_words.jsonl"


def load_dataset(path: Path) -> list[dict]:
    """Reads a JSONL file (one JSON object per line) into a list of dicts.
    Skips and logs any line that fails to parse, instead of crashing
    the whole app over one bad row."""
    entries: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] Skipping bad JSON on line {line_number}: {e}")
    return entries


# Loaded once when this module is first imported (i.e. on app startup),
# not on every request.
DATASET: list[dict] = load_dataset(DATA_PATH)


def search_dataset(query: str) -> list[dict]:
    """Case-insensitive substring search across both 'word' and 'gloss',
    so a user can type either a Bikol word or its English meaning."""
    query = query.strip().lower()
    if not query:
        return []

    results = []
    for entry in DATASET:
        word = str(entry.get("word", "")).lower()
        gloss = str(entry.get("gloss", "")).lower()
        if query in word or query in gloss:
            results.append(entry)
    return results
