# Bikol Speech Preprocessing Pipeline — Architecture

## Overview

```
INPUT DIR
├── manifest.yml
├── MAT_01.mp3
├── interview.mp4
└── ...

      │  python pipeline/run.py input_dir/ output_dir/
      ▼

         ╔════════════════════════════════╗
         ║         run.py                 ║
         ║                                ║
         ║  Stage 1: NORMALIZE (ffmpeg)   ║
         ║  Stage 2: SEGMENT  (ffmpeg)    ║
         ║  Stage 3: CLASSIFY (MMS-LID)   ║
         ║                                ║
         ╚════════════════╤════════════════╝
                          │
OUTPUT DIR
├── audio/*.wav
├── rejected/*.wav
├── manifest.csv
├── rejected.csv
└── pipeline.log
```

The pipeline reads a single `manifest.yml` from the input directory. Each
file goes through three stages. The output receives segmented WAVs with
dual-signal metadata: the user's claimed `dialect_label` alongside MMS-LID's
`predicted_lang`.

---

## CLI

```
python pipeline/run.py <input_dir> <output_dir>

Options:
  --skip-classify   Run only stages 1-2, skip language classification
  --keep-temp       Keep temporary files for debugging
  -v, --verbose     Print per-file progress
```

`output_dir` is cleared before each run. Both arguments are required.

Temp files go to system temp (`/tmp/pipeline_{uuid}/`) and are cleaned after
the run unless `--keep-temp` is passed.

### Run Summary (GPU)

```
$ python pipeline/run.py my_batch/ output/

Stage 1 (normalize):  5/5 files ✓
Stage 2 (segment):    42 segments
Stage 3 (classify):   Using CUDA (NVIDIA GeForce RTX 3060)
                      42/42 classified in 4.2s (31 kept, 11 rejected)

Output:
  output/audio/                     31 segments
  output/rejected/                  11 segments
  output/manifest.csv               31 rows
  output/rejected.csv               11 rows
  output/pipeline.log               58 lines

Done.
```

### Run Summary (CPU)

```
$ python pipeline/run.py my_batch/ output/

Stage 1 (normalize):  5/5 files ✓
Stage 2 (segment):    42 segments
Stage 3 (classify):   Downloading MMS-LID-256 (3.9 GB, one-time)...
                      ⚠ No GPU detected — running on CPU (5-15s/clip)
                      For faster processing, see the Colab fallback below.
                      42/42 classified in 4m 12s (31 kept, 11 rejected)

Output:
  output/audio/                     31 segments
  output/rejected/                  11 segments
  output/manifest.csv               31 rows
  output/rejected.csv               11 rows
  output/pipeline.log               58 lines

Done.
```

### Colab Fallback

If your machine lacks a GPU, the Colab notebook processes Stage 3 on a free
T4 GPU (~100× faster than CPU):

1. Run stages 1-2 locally: `python pipeline/run.py my_batch/ output/ --skip-classify`
2. The segmented WAVs are in `output/audio/`
3. Open `pipeline/validate.ipynb` in [Google Colab](https://colab.research.google.com/)
4. Upload `output/audio/` as a zip → Runtime → Run All
5. Download `manifest.csv` and `rejected.csv`, place in `output/`

---

## Input Contract

### manifest.yml Format

```yaml
# Global defaults — applied to all files unless overridden
defaults:
  dialect_label: naga
  confidence: high
  segment:
    max_duration_s: 10
    min_duration_s: 1

# Per-file entries
files:
  - path: MAT_01.mp3
    source_name: bible-central-bikol

  - path: MAT_02.mp3
    source_name: bible-central-bikol

  - path: interview.mp4
    dialect_label: albay
    confidence: inferred
    source_type: field_recording
```

| Rule | Behavior |
|---|---|
| File listed in `files` | Processed with defaults + per-file overrides |
| File NOT listed in `files` | Skipped with warning |
| Entry has no matching file | Error, skip |
| `defaults` block omitted | Pipeline uses hardcoded fallback defaults |
| `dialect_label` omitted | Pipe through with empty label |

### Manifest Fields

| Field | Values | Description |
|---|---|---|
| `dialect_label` | `naga`, `albay`, or any string | Passed through to output. The pipeline does NOT validate this field. |
| `confidence` | `high`, `medium`, `inferred` | How trustworthy is the label. Propagated to manifest.csv. |
| `source_name` | any string | For provenance. |
| `source_type` | `bible_api`, `app_recording`, `youtube`, `field_recording`, `manual` | How the audio was acquired. |

### Supported Audio Formats

Any format ffmpeg can read: `.mp3`, `.mp4`, `.wav`, `.webm`, `.ogg`, `.m4a`,
`.flac`, `.mov`, `.mkv`, `.aac`, `.opus`, `.wma`, `.3gp`.

Video files are accepted — ffmpeg extracts the first audio stream.

---

## Stage 1: NORMALIZE

### Input → Output

```
{file}.{ext}   (any format)
     │
     ▼
ffmpeg -y -i input -ar 16000 -ac 1 -sample_fmt s16 output.wav
     │
     ▼
/tmp/pipeline_*/normalize/{basename}.wav
```

### Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Resample rate | 16kHz | Standard for speech ML |
| 2 | Channel count | Mono (downmix) | Pipeline doesn't need stereo |
| 3 | Bit depth | Signed 16-bit PCM | Widest compatibility, smallest size |
| 4 | Volume normalization | None | Not the pipeline's job |
| 5 | Audio stream selection | First stream | Default ffmpeg behavior |
| 6 | Corrupted file | Log, skip, continue | Don't abort for one bad file |
| 7 | Wrong extension (mp3 named .wav) | ffmpeg probes container | Works in most cases |
| 8 | Missing audio stream | ffmpeg fails | Logged, skipped |
| 9 | Temp file location | System tmpdir | Cleaned after run |
| 10 | ffmpeg timeout | 5 minutes per file | Prevents hanging |

### Errors

| Error | Cause | Behavior |
|---|---|---|
| `ffmpeg_fail` | Corrupt, unsupported, no audio stream | Log, skip file |
| `ffmpeg_timeout` | File too large, stuck decode | Log, skip |

### Log Entry

```json
{"ts": "2026-06-25T15:00:00", "stage": "normalize", "file": "MAT_01.mp3", "status": "ok", "output": "/tmp/pipeline_*/normalize/MAT_01.wav", "duration_ms": 120000}
```

---

## Stage 2: SEGMENT

### Input → Output

```
/tmp/pipeline_*/normalize/{basename}.wav
     │
     ▼
If duration ≤ max_duration_s  → one segment
If duration > max_duration_s  → split into N chunks of exactly max_duration_s
                                  last chunk: keep if ≥ min_duration_s
     │
     ▼
/tmp/pipeline_*/segment/{basename}_000.wav
...
```

### Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | Method | Hard cut (ffmpeg `-segment_time`) | Simple, no model dependency |
| 2 | Max duration | 10s (configurable) | Long enough for LID |
| 3 | Min duration | 1s (configurable) | Discard noise/clicks |
| 4 | VAD | Skipped | Stage 3 catches silence |
| 5 | Mid-word cuts | Allowed | LID works on sub-second audio |
| 6 | Overlap | None | Clean cuts |

### Configuration

```yaml
segment:
  max_duration_s: 10
  min_duration_s: 1
```

### What Happens Per File

| Duration | Result |
|---|---|
| 0.5s | Discarded |
| 1s | One segment |
| 10s | One segment |
| 45s | Five segments: 4 × 10s + 1 × 5s |
| 41s | Five segments: 4 × 10s + 1 × 1s |
| 30s | Three 10s segments |

### Log Entry

```json
{"ts": "2026-06-25T15:00:01", "stage": "segment", "file": "MAT_01.wav", "status": "ok", "input_duration_ms": 120000, "segments": 12, "avg_duration_ms": 10000}
```

---

## Stage 3: CLASSIFY

### Input → Output

```
/tmp/pipeline_*/segment/{basename}_000.wav
     │
     ▼
Model: facebook/mms-lid-256
     │
     ├── lang ∈ known PH codes → KEEP → output_dir/audio/
     └── otherwise → REJECT → output_dir/rejected/
```

### Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | LID model | `facebook/mms-lid-256` | Only model covering Bikol (`bcl`) |
| 2 | Inference method | HuggingFace `pipeline("audio-classification")` | Simplest integration |
| 3 | Gate logic | PH language filter: `{bcl, bto, ubl, tgl, ceb, ilo, hil, war}` | MMS-LID misclassifies conversational Bikol as Tagalog/Cebuano. Wider gate. `manifest.csv` records both `dialect_label` and `predicted_lang`. |
| 4 | Batching | One segment at a time | Simplest |
| 5 | Model loading | Once at pipeline start | Avoid reloading 4GB per segment |
| 6 | Rejected audio | Saved to `output_dir/rejected/` | Users can inspect false negatives |
| 7 | GPU usage | Auto-detect via `torch.cuda.is_available()` | Falls back to CPU with warning |
| 8 | Model cache | `pipeline/models/` via `cache_dir` | One-time download. gitignored |

### GPU Detection

`validate.py` checks at startup:

```
├── CUDA available?    → GPU     → ~0.1s per clip
├── MPS available?     → MPS     → ~0.3s per clip
└── neither            → CPU     → 5-15s per clip, prints warning
```

### Model Storage

```python
model = pipeline("audio-classification", model="facebook/mms-lid-256",
                 cache_dir="pipeline/models/")
```

| Behavior | Details |
|---|---|
| Default location | `~/.cache/huggingface/` |
| Project convention | `pipeline/models/` |
| Disk size | ~3.9 GB |
| First run | Downloads from HuggingFace |
| Subsequent runs | Loads from cache |

### Accepted Language Codes

**Known PH codes (all pass the gate):**

| Code | Variety |
|---|---|
| `bcl` | Central Bikol (Naga/Coastal) |
| `bto` | Rinconada Bikol |
| `ubl` | Buhi'non Bikol |
| `tgl` | Tagalog |
| `ceb` | Cebuano |
| `ilo` | Ilocano |
| `hil` | Hiligaynon |
| `war` | Waray |

Model coverage verified for `bcl`, `bto`, and `ubl`. The other codes may or
may not be recognized by MMS-LID-256. If unrecognized, segments are rejected
as `not_ph_language`.

### Log Entry

Keep:
```json
{"ts": "2026-06-25T15:00:02", "stage": "classify", "segment": "MAT_01_000.wav", "status": "keep", "lang": "bcl", "score": 0.9421}
```

Reject:
```json
{"ts": "2026-06-25T15:00:03", "stage": "classify", "segment": "MAT_01_005.wav", "status": "reject", "lang": "eng", "score": 0.8732, "reason": "not_ph_language"}
```

---

## Output Schema

### manifest.csv

| Column | Type | Source |
|---|---|---|
| `segment_id` | `{dialect_label}_{counter:05d}` | Generated |
| `wav_path` | `audio/{segment_id}.wav` | Relative path |
| `dialect_label` | string | From manifest.yml |
| `confidence` | `high` \| `medium` \| `inferred` | From manifest.yml |
| `source_name` | string | From manifest.yml |
| `source_type` | string | From manifest.yml |
| `duration_ms` | integer | ffprobe on segment WAV |
| `predicted_lang` | ISO code (e.g. `bcl`) | MMS-LID top-1 |
| `predicted_score` | 0.0–1.0 | MMS-LID confidence |

### rejected.csv

Same columns, plus:

| Column | Type |
|---|---|
| `reject_reason` | `not_ph_language`, `lid_error` |

### pipeline.log

JSONL format. One line per event: `normalize`, `segment`, `classify`.

---

## Project Layout

```
technosprint_2026/
├── web_app/
│   ├── backend/                 # FastAPI + SQLite (port 8000)
│   │   ├── app/...
│   │   ├── data/
│   │   │   └── prompts.csv     # static sentence prompts
│   │   └── requirements.txt
│   ├── frontend/               # Next.js + Tailwind (port 3000)
│   │   └── ...
│   └── .env
│
├── pipeline/                    # CLI tool
│   ├── run.py                   # Entry point
│   ├── normalize.py             # Stage 1: ffmpeg
│   ├── segment.py               # Stage 2: hard-cut
│   ├── validate.py              # Stage 3: MMS-LID
│   ├── manifest.py              # Parse manifest.yml
│   ├── output.py                # Write CSVs + log
│   ├── config.py                # Defaults
│   └── requirements.txt
│
├── pipeline_architecture.md
├── Makefile
├── README.md
└── .gitignore
```

---

## Edge Cases

| Scenario | Behavior |
|---|---|
| No `manifest.yml` in input dir | Error, exit |
| Entry has no matching media file | Error, skip |
| Media file with no `files` entry | Skip with warning |
| `defaults` block omitted | Hardcoded fallbacks |
| All files fail Stage 1 | Empty outputs |
| LID inference timeout (>60s) | Reject as `lid_timeout` |
| Pipeline interrupted (Ctrl+C) | Temp files remain (`--keep-temp`) |
| Output dir exists from previous run | Auto-cleared |
| Empty audio file (0 bytes) | Fails Stage 1 |

---

## Dependencies

```
transformers>=4.45.0
torch>=2.5.0
soundfile>=0.12.0
librosa>=0.10.0
pyyaml>=6.0
```

`ffmpeg` must be installed on the system.

---

## Deferred

| Item | Why |
|---|---|
| Downloading/scraping audio | Out of scope. Users provide files. |
| Sidecar JSON per file | Replaced by single `manifest.yml`. |
| VAD-based segmentation | Hard-cut approach chosen. |
| ONNX LID model | HF pipeline works. |
| Transcription | Pipeline is for preprocessing, not ASR. |
| Dialect classification model | Pipeline output is training data for such models. |
| Web UI for pipeline | CLI only. |
| Multi-language support | Bikol-specific. Changing ISO codes changes language. |
