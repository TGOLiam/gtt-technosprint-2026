from pathlib import Path

DEFAULTS = {
    "segment": {
        "max_duration_s": 10,
        "min_duration_s": 1,
    },
}

MODEL_ID = "facebook/mms-lid-256"
MODEL_CACHE_DIR = str(Path(__file__).resolve().parent / "models")

KNOWN_PH_LANGS = ["bcl", "bto", "ubl", "tgl", "ceb", "ilo", "hil", "war"]
