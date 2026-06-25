import subprocess
import uuid
from pathlib import Path

import soundfile as sf

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw_recordings"
WAV_DIR = DATA_DIR / "audio"
TARGET_SR = 16000


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    WAV_DIR.mkdir(parents=True, exist_ok=True)


def save_upload(blob: bytes, original_format: str) -> str:
    ensure_dirs()
    rec_id = str(uuid.uuid4())
    ext = original_format.split(";")[0].split("/")[-1] if original_format else "webm"
    raw_path = RAW_DIR / f"{rec_id}.{ext}"
    raw_path.write_bytes(blob)
    return rec_id, str(raw_path)


def convert_to_wav(raw_path: str, rec_id: str) -> str | None:
    ensure_dirs()
    wav_path = WAV_DIR / f"{rec_id}.wav"
    result = subprocess.run([
        "ffmpeg", "-y", "-i", raw_path,
        "-ar", str(TARGET_SR), "-ac", "1", "-sample_fmt", "s16",
        str(wav_path),
    ], capture_output=True, text=True)

    if wav_path.exists() and wav_path.stat().st_size > 0:
        return str(wav_path)
    return None


def get_duration_ms(wav_path: str) -> int:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", wav_path,
    ], capture_output=True, text=True)
    try:
        return int(float(result.stdout.strip()) * 1000)
    except (ValueError, TypeError):
        return 0


def is_silent(wav_path: str, threshold: float = 0.005) -> bool:
    import numpy as np
    try:
        data, _ = sf.read(wav_path, dtype="float32")
    except Exception:
        return True
    if data.size == 0:
        return True
    return float(np.abs(data).mean()) < threshold
