# TinigBicol — Bikol Speech Preprocessing Pipeline

A reproducible CLI tool that transforms raw labeled audio into validated,
structured Bikol dialect speech data.

Drop a folder of audio files and a `manifest.yml` — get standardized 16kHz
WAV segments with language classification and structured metadata back.

---

## How It Works

```
testing/test_input/               ← your audio + manifest.yml
     │
     ▼
Stage 1 ─── NORMALIZE
            ffmpeg → 16kHz mono WAV. Any format accepted.
     │
     ▼
Stage 2 ─── SEGMENT
            Hard-cut into 10s chunks. Silent/unlabeled noise discarded.
     │
     ▼
Stage 3 ─── CLASSIFY
            MMS-LID-256 predicts language. Philippine speech kept,
            non-PH speech rejected.
     │
     ▼
testing/test_output/
├── audio/naga_00001.wav          ← kept segments
├── rejected/eng_00015.wav        ← rejected segments
├── manifest.csv                  ← metadata: your label + model prediction
├── rejected.csv
└── pipeline.log                  ← full provenance (JSONL)
```

Each segment in `manifest.csv` carries two signals:

| Column | Meaning |
|---|---|
| `dialect_label` | What you claimed (from manifest.yml) |
| `predicted_lang` | What MMS-LID heard (ISO code) |
| `predicted_score` | How confident the model was (0–1) |

The gate is a Philippine language filter — any PH code passes. Non-PH
predictions (English, Japanese, noise) are rejected. The dual-signal
output lets you decide whose signal to trust.

---

## Quick Start

### Prerequisites

- Python 3.11+
- ffmpeg

### Run the pipeline

```bash
# Install dependencies (one time)
pip install -r pipeline/requirements.txt

# Run with sample config
./run.sh testing/test_input/ testing/test_output/
```

First run downloads MMS-LID-256 (~3.9 GB, cached thereafter). GPU is
auto-detected. On CPU, expect 5–15s per 10s segment.

### Use your own audio

1. Drop audio files into a directory (any format — mp3, mp4, wav, webm, etc.)
2. Create a `manifest.yml` listing each file with its dialect label:

```yaml
defaults:
  confidence: high

files:
  - path: recording.mp3
    dialect_label: naga
    source_name: my-field-recording
    source_type: field_recording
```

3. Run:

```bash
./run.sh my_audio/ my_output/
```

See `testing/test_input/manifest.yml` for a full example with all options.

### Skip classification (fast local-only run)

```bash
./run.sh my_audio/ my_output/ --skip-classify
```

Runs stages 1–2 (normalize + segment) without MMS-LID. Use the Colab
fallback for classification later:

1. Open `pipeline/validate.ipynb` in Google Colab
2. Upload `my_output/audio/` as a zip
3. Runtime → Run All → download CSVs

---

## Project Layout

```
├── pipeline/              # The CLI tool
│   ├── run.py             # Entry point
│   ├── normalize.py       # Stage 1: ffmpeg
│   ├── segment.py         # Stage 2: hard-cut
│   ├── validate.py        # Stage 3: MMS-LID
│   ├── manifest.py        # Parse manifest.yml
│   ├── output.py          # Write CSVs + log
│   ├── config.py          # Defaults
│   └── requirements.txt
│
├── testing/               # Sample input/output
│   ├── test_input/
│   │   └── manifest.yml   # Sample config
│   └── test_output/
│
├── web_app/               # Optional: community recording app
│   ├── backend/           # FastAPI + SQLite (port 8000)
│   └── frontend/          # Next.js + Tailwind (port 3000)
│
├── run.sh / run.bat       # Cross-platform launcher
├── pipeline_architecture.md
└── README.md
```

---

## Optional: Web App

A community recording interface that feeds into the pipeline. Users select
their dialect, record sentences from a prompt list, and submit.

### Quick Start

```bash
cd web_app/backend && pip install -r requirements.txt
cd web_app/frontend && npm install

# Terminal 1 — backend
cd web_app/backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd web_app/frontend && npm run dev
```

| Endpoint | Description |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/prompt?dialect=naga` | Get next recording prompt |
| `POST /api/record` | Submit audio (multipart) |
| `GET /api/stats` | Dashboard statistics |

Recordings are stored in `web_app/backend/data/audio/`. To feed them
into the pipeline, create a `manifest.yml` pointing to those WAV files
with `source_type: app_recording`.

---

## Background

Bikol is a Philippine macrolanguage with multiple dialect varieties
(Naga/Coastal, Albay/Inland, Rinconada, and others). Despite millions of
speakers, no publicly available speech dataset labels these varieties.
This pipeline produces the first open, reproducible tool for building
Bikol dialect speech datasets from arbitrary audio sources.

See `pipeline_architecture.md` for the full specification, including
design decisions, edge cases, and model limitations.
