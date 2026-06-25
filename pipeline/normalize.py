import subprocess
from pathlib import Path


def normalize(input_path, basename, temp_dir):
    """Convert any audio/video to 16kHz mono WAV. Returns output path or None."""
    output_dir = Path(temp_dir) / "normalized"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{basename}.wav"

    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(input_path),
            "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
            str(output_path),
        ], capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

    if output_path.exists() and output_path.stat().st_size > 0:
        return output_path
    return None
