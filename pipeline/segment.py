import subprocess
from pathlib import Path


def get_duration_ms(wav_path):
    """Get duration of a WAV file in milliseconds."""
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path),
    ], capture_output=True, text=True, timeout=10)

    try:
        return int(float(result.stdout.strip()) * 1000)
    except (ValueError, TypeError):
        return 0


def segment(wav_path, segment_config, temp_dir):
    """Hard-cut a WAV into chunks. Returns list of segment paths."""
    max_s = segment_config.get("max_duration_s", 10)
    min_s = segment_config.get("min_duration_s", 1)

    duration_ms = get_duration_ms(wav_path)
    duration_s = duration_ms / 1000.0

    if duration_s <= 0:
        return []

    if duration_s < min_s:
        return []

    if duration_s <= max_s:
        return [wav_path]

    output_dir = Path(temp_dir) / "segmented" / wav_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-f", "segment", "-segment_time", str(max_s),
        "-c", "copy", str(output_dir / f"{wav_path.stem}_%03d.wav"),
    ], capture_output=True, text=True, timeout=60)

    segments = sorted(output_dir.glob("*.wav"))

    if segments:
        last_dur_s = get_duration_ms(segments[-1]) / 1000.0
        if last_dur_s < min_s:
            segments[-1].unlink()
            segments = segments[:-1]

    return segments
