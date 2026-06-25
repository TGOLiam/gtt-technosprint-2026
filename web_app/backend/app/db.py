import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "metadata.db"
PROMPTS_CSV = Path(__file__).resolve().parent.parent / "data" / "prompts.csv"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS prompts (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            dialect_variant TEXT DEFAULT '',
            category TEXT DEFAULT 'general',
            source TEXT DEFAULT '',
            times_served INTEGER DEFAULT 0,
            times_recorded INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS speakers (
            id TEXT PRIMARY KEY,
            dialect_label TEXT NOT NULL,
            municipality TEXT DEFAULT '',
            age_range TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            license_choice TEXT DEFAULT 'cc0',
            consent_granted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recordings (
            id TEXT PRIMARY KEY,
            speaker_id TEXT REFERENCES speakers(id),
            prompt_id TEXT,
            wav_path TEXT NOT NULL,
            original_format TEXT DEFAULT '',
            duration_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn


def seed_prompts():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    if not PROMPTS_CSV.exists():
        print(f"  No prompts.csv at {PROMPTS_CSV}, inserting fallback prompts")
        fallbacks = [
            ("p0001", "Magayon an panahon ngunyan.", "", "general", "fallback"),
            ("p0002", "Salamat sa saimong tabang.", "", "general", "fallback"),
            ("p0003", "Harong mi ini sa Naga.", "naga", "diagnostic", "fallback"),
            ("p0004", "Balay mi ini sa Legazpi.", "albay", "diagnostic", "fallback"),
            ("p0005", "Pwede tabi akong maghapot?", "", "general", "fallback"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO prompts VALUES (?, ?, ?, ?, ?, 0, 0)",
            fallbacks,
        )
    else:
        with open(PROMPTS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [(r["id"], r["text"], r.get("dialect_variant", ""),
                     r.get("category", "general"), r.get("source", ""))
                    for r in reader]
        conn.executemany(
            "INSERT OR IGNORE INTO prompts VALUES (?, ?, ?, ?, ?, 0, 0)",
            rows,
        )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    print(f"  Seeded {count} prompts")
    conn.close()
