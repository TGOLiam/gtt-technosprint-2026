import warnings

import torch
from transformers import pipeline
from transformers.utils import logging as transformers_logging

from pipeline.config import MODEL_ID, KNOWN_PH_LANGS

transformers_logging.set_verbosity_error()
warnings.filterwarnings("ignore", message="You are sending unauthenticated requests")


def detect_device():
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model(cache_dir):
    device = detect_device()
    if device == "cpu":
        print("  \u26a0 No GPU detected \u2014 running on CPU (5-15s/clip)")
        print("    For faster processing, see the Colab fallback in the README.")
    else:
        print(f"  Using {device.upper()}")

    model = pipeline(
        "audio-classification",
        model=MODEL_ID,
        cache_dir=cache_dir,
        device=0 if device != "cpu" else -1,
    )
    return model


def classify(model, wav_path):
    """Run language identification on a single WAV segment.

    Returns dict with keys: lang (ISO code), score (0-1), is_ph (bool).
    On error, returns lang="" and score=0.0.
    """
    try:
        result = model(str(wav_path))[0]
    except Exception:
        return {"lang": "", "score": 0.0, "is_ph": False}

    lang = result["label"]
    score = round(result["score"], 4)
    is_ph = lang in KNOWN_PH_LANGS

    return {"lang": lang, "score": score, "is_ph": is_ph}
