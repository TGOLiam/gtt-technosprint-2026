import json
import re
import subprocess
from pathlib import Path

import requests
import soundfile as sf
import yaml

RAW = Path("data/raw")
SR = 16000


def mkdir(p):
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_sources(path="sources.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


# ---- downloaders (each returns file count) ----


def dl_huggingface(s, dialect):
    out = mkdir(RAW / s["name"])
    try:
        from datasets import load_dataset
    except ImportError:
        print(f"  SKIP: datasets not installed")
        return 0

    try:
        ds = load_dataset(s["id"], split="train")
    except Exception:
        try:
            ds = load_dataset(s["id"], split="train", trust_remote_code=True)
        except Exception as e:
            print(f"  FAIL: {e}")
            return 0

    n = 0
    for i, row in enumerate(ds):
        try:
            audio = row["audio"]
            arr = audio["array"]
            orig_sr = audio["sampling_rate"]
            if arr.ndim > 1:
                arr = arr[:, 0]
            if orig_sr != SR:
                import librosa
                arr = librosa.resample(arr, orig_sr=orig_sr, target_sr=SR)
            wav = out / f"{i:04d}.wav"
            sf.write(str(wav), arr, SR)
            meta = {"source": s["name"], "type": "huggingface", "dialect": dialect,
                    "confidence": s["confidence"], "index": i}
            json.dump(meta, (out / f"{i:04d}.json").open("w"), ensure_ascii=False, indent=2)
            n += 1
        except Exception:
            pass
    return n


def dl_direct(s, dialect):
    out = mkdir(RAW / s["name"])
    url = s["url"]

    if "globalrecordings" in url:
        try:
            html = requests.get(url, timeout=30).text
            mp3s = re.findall(r'href="([^"]+\.mp3)"', html)
            n = 0
            for i, rel in enumerate(mp3s):
                mp3_url = rel if rel.startswith("http") else "https://globalrecordings.net" + rel
                mp3 = out / f"{i:04d}.mp3"
                r = requests.get(mp3_url, timeout=120)
                mp3.write_bytes(r.content)
                meta = {"source": s["name"], "type": "direct_download", "dialect": dialect,
                        "confidence": s["confidence"], "index": i, "url": mp3_url}
                json.dump(meta, (out / f"{i:04d}.json").open("w"), ensure_ascii=False, indent=2)
                n += 1
                print(f"    [{n}] {len(r.content)//1024}KB")
            return n
        except Exception as e:
            print(f"  FAIL: {e}")
            return 0

    try:
        r = requests.get(url, timeout=120)
        ext = url.rsplit(".", 1)[-1][:5]
        (out / f"dl.{ext}").write_bytes(r.content)
        meta = {"source": s["name"], "type": "direct_download", "dialect": dialect,
                "confidence": s["confidence"], "url": url}
        json.dump(meta, (out / "dl.json").open("w"), ensure_ascii=False, indent=2)
        return 1
    except Exception as e:
        print(f"  FAIL: {e}")
        return 0


def dl_bible(s, dialect):
    out = mkdir(RAW / s["name"])
    iso = s["iso"]
    n = 0
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://live.bible.is/"}

    for book in ["MAT", "MRK", "LUK", "JHN", "ACT"]:
        for ch in range(1, 50):
            mp3 = out / f"{book}_{ch:02d}.mp3"
            if mp3.exists():
                n += 1
                continue

            worked = False
            for url_fmt in [
                f"https://cloud.faithcomesbyhearing.com/audio-bibles/{iso}/mp3/{book}_{ch:02d}.mp3",
                f"https://cloud.faithcomesbyhearing.com/audio-bibles/{iso}/mp3/{book}_{ch:02d}_{iso}.mp3",
            ]:
                try:
                    r = requests.get(url_fmt, headers=headers, timeout=60)
                    if r.status_code == 200 and len(r.content) > 10000:
                        mp3.write_bytes(r.content)
                        meta = {"source": s["name"], "type": "bible_api", "dialect": dialect,
                                "confidence": s["confidence"], "iso": iso, "book": book, "chapter": ch}
                        json.dump(meta, (out / f"{book}_{ch:02d}.json").open("w"), ensure_ascii=False, indent=2)
                        n += 1
                        worked = True
                        break
                except Exception:
                    continue

            if not worked:
                break
    return n


def dl_ytdlp(s, dialect):
    out = mkdir(RAW / s["name"])
    url = s["url"]
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "wav", "--audio-quality", "0",
        "-o", str(out / "%(id)s.%(ext)s"), "--no-playlist", url,
    ], check=False, timeout=300)
    return len(list(out.glob("*.wav")))


def dl_ytdlp_search(s, dialect):
    out = mkdir(RAW / s["name"])
    query = s["query"]
    n = s.get("max_videos", 10)
    subprocess.run([
        "yt-dlp", f"ytsearch{n}:{query}",
        "-x", "--audio-format", "wav", "--audio-quality", "0",
        "-o", str(out / "%(id)s.%(ext)s"), "--no-playlist",
    ], check=False, timeout=600)
    return len(list(out.glob("*.wav")))


def dl_radio(s, dialect):
    url = s.get("url", "")
    if not url:
        print(f"  SKIP: no URL configured")
        return 0
    out = mkdir(RAW / s["name"])
    dur = s.get("capture_seconds", 1800)
    wav = out / "stream.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", url, "-t", str(dur),
        "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", str(wav),
    ], check=False, capture_output=True, timeout=dur + 30)
    if wav.exists():
        meta = {"source": s["name"], "type": "radio_stream", "dialect": dialect,
                "confidence": s["confidence"], "url": url, "capture_s": dur}
        json.dump(meta, (out / "stream.json").open("w"), ensure_ascii=False, indent=2)
        return 1
    return 0


DISPATCH = {
    "huggingface": dl_huggingface,
    "direct_download": dl_direct,
    "bible_api": dl_bible,
    "ytdlp": dl_ytdlp,
    "ytdlp_search": dl_ytdlp_search,
    "radio_stream": dl_radio,
}


def main():
    sources = load_sources()
    total = 0

    for dialect in ["naga", "albay"]:
        print(f"\n{'='*50}")
        print(f"  {dialect.upper()}")
        print(f"{'='*50}")
        for s in sources[dialect]:
            if not s.get("audio", True):
                print(f"  [{dialect}] {s['name']}: text source, skip")
                continue
            fn = DISPATCH.get(s["type"])
            if fn is None:
                print(f"  [{dialect}] {s['name']}: unknown type '{s['type']}'")
                continue
            print(f"  [{dialect}] {s['name']} ({s['type']})...")
            n = fn(s, dialect)
            print(f"    -> {n} files")
            total += n

    print(f"\n{'='*50}")
    print(f"  TOTAL: {total} audio files")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
