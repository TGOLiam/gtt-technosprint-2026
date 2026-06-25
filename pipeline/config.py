from pathlib import Path

DEFAULTS = {
    "segment": {
        "max_duration_s": 10,
        "min_duration_s": 1,
    },
    "validate": {
        "accepted_langs": ["bcl", "bik", "ubl", "rbl", "fbl", "bto", "bln", "cts", "lbl"],
        "min_score": 0.3,
    },
}

MODEL_ID = "facebook/mms-lid-256"
MODEL_CACHE_DIR = str(Path(__file__).resolve().parent / "models")
