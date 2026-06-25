import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_FIELDS = [
    "segment_id", "wav_path", "dialect_label", "confidence",
    "source_name", "source_type", "duration_ms", "bikol_lang", "bikol_score",
]

REJECTED_FIELDS = MANIFEST_FIELDS + ["reject_reason"]


class OutputWriter:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.audio_dir = self.output_dir / "audio"
        self.rejected_dir = self.output_dir / "rejected"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.rejected_dir.mkdir(parents=True, exist_ok=True)

        self._log_path = self.output_dir / "pipeline.log"
        self._manifest_rows = []
        self._rejected_rows = []
        self._counter = {}

    def log(self, stage, name, status, **kwargs):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "file": name,
            "status": status,
            **kwargs,
        }
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def add_manifest_row(self, entry, wav_path, lang, score, duration_ms):
        label = entry.get("dialect_label", "")
        self._counter[label] = self._counter.get(label, 0) + 1
        seg_id = f"{label}_{self._counter[label]:05d}" if label else f"unk_{self._counter.get(label, 0):05d}"

        dest = self.audio_dir / f"{seg_id}.wav"
        shutil.copy2(wav_path, dest)

        self._manifest_rows.append({
            "segment_id": seg_id,
            "wav_path": f"audio/{seg_id}.wav",
            "dialect_label": label,
            "confidence": entry.get("confidence", "inferred"),
            "source_name": entry.get("source_name", ""),
            "source_type": entry.get("source_type", "manual"),
            "duration_ms": duration_ms,
            "bikol_lang": lang,
            "bikol_score": score,
        })

    def add_rejected_row(self, entry, wav_path, reason, lang="", score=0.0, duration_ms=0):
        label = entry.get("dialect_label", "")
        dest = self.rejected_dir / wav_path.name
        shutil.copy2(wav_path, dest)

        row = {
            "segment_id": f"rej_{wav_path.stem}",
            "wav_path": f"rejected/{wav_path.name}",
            "dialect_label": label,
            "confidence": entry.get("confidence", "inferred"),
            "source_name": entry.get("source_name", ""),
            "source_type": entry.get("source_type", "manual"),
            "duration_ms": duration_ms,
            "bikol_lang": lang,
            "bikol_score": score,
            "reject_reason": reason,
        }
        self._rejected_rows.append(row)

    def write(self):
        if self._manifest_rows:
            self._write_csv(self.output_dir / "manifest.csv", self._manifest_rows, MANIFEST_FIELDS)
        if self._rejected_rows:
            self._write_csv(self.output_dir / "rejected.csv", self._rejected_rows, REJECTED_FIELDS)

    def _write_csv(self, path, rows, fields):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
