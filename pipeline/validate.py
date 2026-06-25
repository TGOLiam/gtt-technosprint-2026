import torch
from pathlib import Path
from transformers import pipeline

from pipeline.config import MODEL_ID, DEFAULTS


def detect_device():
    """Return device string for transformers pipeline."""
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model(cache_dir):
    """Load MMS-LID-256 model. Call once at pipeline start."""
    device = detect_device()
    if device == "cpu":
        print("  ⚠ No GPU detected — running on CPU (5-15s/clip)")
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


def validate(model, wav_path, validate_config):
    """Run language identification on a single WAV segment.
    
    Returns dict with keys: status ("keep"|"reject"), top_lang (ISO code),
    score (0-1). On reject, also includes "reason".
    """
    accepted = validate_config.get("accepted_langs", DEFAULTS["validate"]["accepted_langs"])
    min_score = validate_config.get("min_score", DEFAULTS["validate"]["min_score"])

    try:
        result = model(str(wav_path))[0]
    except Exception as e:
        return {"status": "reject", "reason": "lid_error", "error": str(e), "top_lang": "", "score": 0.0}

    lang = result["label"]
    score = round(result["score"], 4)

    if lang not in accepted:
        return {"status": "reject", "top_lang": lang, "score": score, "reason": "not_bikol"}
    if score < min_score:
        return {"status": "reject", "top_lang": lang, "score": score, "reason": "low_confidence"}
    return {"status": "keep", "top_lang": lang, "score": score}
