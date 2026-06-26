# TinigBicol — Bikol Speech Preprocessing Pipeline

Despite being spoken by millions across the Bicol Region, Bikol remains almost entirely absent from open speech technology. lLittle to no publicly available datasets. No benchmark. No baseline. Every Filipino voice deserves to be heard — and that starts with building the infrastructure to capture it.

TinigBicol transforms raw Bikol-language audio and video into structured, annotated speech segments — ready for ASR research, dialect study, and dataset construction. Drop a folder of audio files and a `manifest.yml` — get standardized 16kHz WAV segments with language annotation and structured metadata back.

```bash
python tinigbicol.py pipeline <input_dir> <output_dir>   # run the pipeline
python tinigbicol.py serve                                # start the dashboard
```

---

## How It Works
web_app/backend/data/input/       ← raw audio from app + manifest.yml

↓

Stage 1 ─── NORMALIZE

ffmpeg → 16kHz mono WAV. Any format accepted.

↓

Stage 2 ─── SEGMENT

Hard-cut into 10s chunks. Silent/unlabeled noise discarded.

↓

Stage 3 ─── CLASSIFY

MMS-LID-256 predicts language. Philippine speech kept,

non-PH speech rejected.

↓

web_app/backend/data/audio/

├── naga_00001.wav                ← kept segments

├── rejected/eng_00015.wav        ← rejected segments

├── manifest.csv                  ← metadata: your label + model prediction

├── rejected.csv

└── pipeline.log                  ← full provenance (JSONL)

Each segment in `manifest.csv` carries two signals:

| Column | Meaning |
|---|---|
| `dialect_label` | What you claimed (from manifest.yml) |
| `predicted_lang` | What MMS-LID heard (ISO code) |
| `predicted_score` | How confident the model was (0–1) |

The gate is a Philippine language filter — any PH code passes. Non-PH predictions (English, Japanese, noise) are rejected. The dual-signal output lets you decide whose signal to trust.

---

## Quick Start

### Prerequisites

- Python 3.11+
- ffmpeg
- CUDA-Compatible GPU (Optional)

### 1. Use Your Own Audio

Drop audio files into a directory (any format — mp3, mp4, wav, webm, etc.). Create a `manifest.yml` listing each file with its dialect label:

```yaml
defaults:
  confidence: high

files:
  - path: recording.mp3
    dialect_label: naga
    source_name: my-field-recording
    source_type: field_recording
```

See `testing/test_input/manifest.yml` for a full example with all options.

### 2. Run Locally

```bash
# Install dependencies (one time)
python -m pip install -r pipeline/requirements.txt

# Run the full pipeline
python tinigbicol.py pipeline my_audio/ my_output/
```

First run downloads MMS-LID-256 (~3.9 GB, cached thereafter). GPU is auto-detected. On CPU, expect 5–15s per 10s segment.

### 3. Run with Google Colab

If your machine lacks a GPU, offload Stage 3 to Colab's free T4:

```bash
# Run stages 1–2 locally (fast, CPU-friendly)
python tinigbicol.py pipeline my_audio/ my_output/ --skip-classify

# Then:
# 1. Zip the WAVs: zip -r audio.zip my_output/audio/
# 2. Open pipeline/validate.ipynb in Google Colab
# 3. Upload audio.zip → Runtime → Run All
# 4. Download manifest.csv + rejected.csv → place in my_output/
```

Colab processes ~100× faster than CPU and requires no local ML dependencies.

### 4. Skip Inference

Run only stages 1–2 (normalize + segment) without any language classification:

```bash
python tinigbicol.py pipeline my_audio/ my_output/ --skip-classify
```

---

## Project Layout

```sh
tinigbicol.py             # Centralized entry point (pipeline | serve)

pipeline/                 # The CLI tool
│   ├── run.py             # Pipeline entry point
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
├── web_app/               # Community recording app
│   ├── backend/           # FastAPI + SQLite (port 8000)
│   │   └── data/
│   │       ├── input/     # Raw audio uploads + manifest.yml (auto-generated)
│   │       └── audio/     # Pipeline output WAVs
│   └── frontend/          # Next.js + Tailwind (port 3000)
│
├── pipeline_architecture.md
│
└── README.md
```

---

## Web App

A community recording interface that feeds directly into the pipeline. Users select their dialect, record sentences from a prompt list, and submit. Each submission is automatically saved to `web_app/backend/data/input/` and appended to `manifest.yml` — ready for the pipeline to consume.

### Quick Start

```bash
# Install dependencies
cd web_app/backend && python -m pip install -r requirements.txt
cd web_app/frontend && npm install

# Start both servers
cd ../.. && python tinigbicol.py serve
```

Backend: http://localhost:8000  |  Frontend: http://localhost:3000

Ctrl+C stops both servers.

Or use the Makefile:

```bash
make dev
```

| Endpoint | Description |
|---|---|
| `GET /api/health` | Health check (tests DB connection) |
| `GET /api/prompt?dialect=naga` | Get next recording prompt |
| `POST /api/record` | Submit audio (multipart, rate limited: 10/min) |
| `GET /api/stats` | Dashboard statistics |

### Data Flow
User records audio (browser)

↓

POST /api/record

↓

Raw audio saved to data/input/{rec_id}.webm

↓

Entry auto-appended to data/input/manifest.yml

↓

Pipeline: python tinigbicol.py pipeline data/input/ data/audio/

---

## Background

Bikol is a Philippine macrolanguage with multiple dialect varieties (Naga/Coastal, Albay/Inland, Rinconada, and others). Despite millions of speakers, no publicly available speech dataset labels these varieties. This pipeline produces the first open, reproducible tool for building Bikol dialect speech datasets from arbitrary audio sources.

See `pipeline_architecture.md` for the full specification, including design decisions, edge cases, and model limitations.

## AI Disclosure
ChatGPT, Claude, and Meta AI (Facebook MMS-LID-2056) were used to assist in brainstorming, writing refinement, and content organization. All AI-generated outputs were reviewed, edited, and validated by the team, and all final content and decisions remain the responsibility of the authors.

