Got it. Rewriting now.

---

# Tinig Bicol

**A reproducible pipeline for collecting and preprocessing structured Bikol dialect speech data.**

Tinig Bicol provides a preprocessing pipeline that transforms raw labeled audio into validated, structured speech datasets suitable for ASR, TTS, and NLP research on the Bikol language. Optionally, a deployable web app lets you crowdsource audio recordings from your community.

---

## The Pipeline

The core artifact. Takes any labeled audio source and produces validated, structured Bikol speech segments.

### Input

Audio sources registered in `sources.yaml` — YouTube videos, radio streams, Bible audio, field recordings, or app-recorded contributions. Each source carries a `confidence` tag and a dialect label.

### Stages

```
raw media (any format, any source)
     │
     ▼
Stage 1 ─── NORMALIZATION
            Resample to 16kHz mono, convert to WAV.
     │
     ▼
Stage 2 ─── SEGMENTATION
            Split into 3–10 second utterances.
            Silence and noise discarded.
     │
     ▼
Stage 3 ─── VALIDATION
            Verify segments contain Bikol speech.
            English and Tagalog segments rejected.
     │
     ▼
pipeline/output/
├── audio/{nag,alb}_*.wav    Validated speech segments
├── manifest.csv             Structured metadata per segment
├── rejected.csv             Rejected segments
└── pipeline.log             Full provenance (JSONL)
```

### Output Schema

`manifest.csv` fields: `segment_id`, `wav_path`, `dialect_label`, `confidence`, `bikol_lang` (ISO code), `bikol_score`, `source_type`, `source_name`, `duration_ms`, `sample_rate`.

### Running the Pipeline

```bash
python scraper/scrape_audio.py     # Download raw audio
python scraper/postprocess.py      # Normalize → segment → validate
```

Add your own sources to `sources.yaml` and re-run. To adapt for another Philippine language, change the target ISO codes in the validation stage.

---

## Optional: Web App for Community Collection

A deployable web app (FastAPI + Next.js) that lets you collect audio recordings from community members through a browser interface. Recordings feed directly into the pipeline.

### API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/prompt?dialect=naga\|albay` | Get next sentence prompt |
| POST | `/api/record` | Submit audio recording (multipart) |
| GET | `/api/stats` | Dashboard statistics |

### POST /api/record fields

| Field | Required | Description |
|---|---|---|
| `audio` | yes | Audio blob (webm/wav/mp4) |
| `dialect_label` | yes | `naga` or `albay` |
| `prompt_id` | no | Sentence ID being read |
| `speaker_id` | no | Existing speaker UUID |
| `municipality` | no | Speaker's town/city |
| `age_range` | no | Speaker age bracket |
| `gender` | no | Speaker gender |
| `consent_granted` | no | `true` / `false` |

---

## Prerequisites

- Python 3.11+
- ffmpeg
- Node.js 18+ *(web app only)*
- pip

## Project Layout

```
├── frontend-nextjs/     Next.js 16 + React 19 + Tailwind CSS v4
├── backend/             FastAPI + SQLite (port 8000)
├── scraper/             Audio pipeline
├── Makefile             install, dev, test, build, clean
└── .env.example         Shared env vars
```

## Quick Start

### Pipeline only

```bash
pip install -r backend/requirements.txt
python scraper/scrape_audio.py
python scraper/postprocess.py
```

### Full stack (pipeline + web app)

```bash
make install
make dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Testing

```bash
make test
cd backend && pytest -xvs
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for Render deploy instructions.

---

## Who This Is For

- **Developers and NLP researchers** building ASR, TTS, or language models for Bikol
- **Linguists and academics** studying Bikol dialect variation
- **Cultural organizations** building a structured archive of Bikol speech

---

## Background

Bikol is a regional Philippine language with multiple dialects (Naga, Albay, among others). Despite a substantial speaker population, it remains underrepresented in speech datasets, limiting the development of language technologies that could support the language long-term. Tinig Bicol addresses the dataset gap directly.

---

Paste this wherever you need it. Let me know if any section needs adjustment.