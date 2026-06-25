# Group Name: GTT
## Project: Tinig Bicol

## Preserving the Bicol Lanuage, One Word at a Time
Members:
Ebron, Pocsidio, Nadela, Serrano

## Project Case: Tinig sa Liwanag

## Overview

Tinig Bicol is an open, community-driven repository dedicated to preserving and documenting the Bikol language. The platform enables native speakers and community members to contribute words, translations, example sentences, dialect variations, and authentic audio recordings.

At its current stage, Tinig Bicol focuses on collecting and organizing high-quality language data that can serve as a foundation for future research, educational tools, and language technologies. By building a structured data pipeline, the project aims to support future developers, researchers, and initiatives working to preserve and promote the language.

## The Pipeline Artifact

The core hackathon contribution is a **reproducible preprocessing
pipeline** that transforms raw labeled media into validated, structured
Bikol dialect speech data.

### Input

Any audio source with a dialect label — YouTube videos, radio streams,
Bible audio, field recordings, or app-recorded contributions. Sources
are registered in `sources.yaml` with a `confidence` tag.

### Pipeline Stages

```
raw media (any format, any source)
     │
     ▼
Stage 1 ─── NORMALIZATION
            Resample to 16kHz mono, convert to WAV.
            Any audio/video format accepted.
     │
     ▼
Stage 2 ─── SEGMENTATION
            Split long recordings into 3-10 second utterances.
            Silence and noise discarded.
     │
     ▼
Stage 3 ─── VALIDATION
            Verify segments contain Bikol speech.
            Non-Bikol audio (English, Tagalog) rejected.
     │
     ▼
pipeline/output/
├── audio/{nag,alb}_*.wav    Validated speech segments
├── manifest.csv             Structured metadata per segment
├── rejected.csv             Segments that failed validation
└── pipeline.log             Full provenance (JSONL)
```

### Output Schema

`manifest.csv`: `segment_id`, `wav_path`, `dialect_label`, `confidence`,
`bikol_lang` (ISO code), `bikol_score` (validation confidence),
`source_type`, `source_name`, `duration_ms`, `sample_rate`.

### Reproducibility

Anyone can add their own audio sources to `sources.yaml` and re-run:

```bash
python scraper/scrape_audio.py     # Download raw audio
python scraper/postprocess.py      # Normalize → segment → validate
```

The Bikol language filter is configurable. To adapt for another Philippine
language, change the target ISO codes in the validation stage.

## The Problem

Many younger Bikolanos are growing up with limited exposure to their native language due to urbanization, migration, and the dominance of Filipino and English in daily communication.

While some language resources exist, there is currently no centralized, community-powered platform that documents Bikol vocabulary alongside authentic pronunciation and real-world usage.

As a result, valuable linguistic and cultural knowledge is at risk of being lost over time.

## Our Solution 

Tinig Bicol provides a platform where the community itself becomes the steward of language preservation.

Users can:

- Contribute Bikol words and definitions
- Upload authentic audio pronunciations
- Provide sentence examples and usage contexts
- Document dialect-specific variations
- Explore and learn from community-contributed content

Every contribution helps expand a growing repository of Bikol linguistic knowledge.

## Innovation

Unlike traditional dictionaries, Tinig Bicol is built around community participation and audio-based documentation.

The platform not only preserves words but also captures how they are spoken and used in everyday life. Over time, these contributions form a structured dataset that can support:

- Language learning applications
- Academic and linguistic research
- Speech recognition systems
- Text-to-speech technologies
- Future AI models for the Bikol language

By preserving language data today, Tinig Bicol helps lay the foundation for future technologies that can better support regional Philippine languages.

## Target Users

- Native Bikol speakers
- Young Bikolanos learning or reconnecting with the language
- Students and educators
- Researchers and linguists
- Cultural heritage organizations

## Vision

To build the largest community-driven repository of Bikol language resources and ensure that the language remains accessible, relevant, and preserved for future generations.

## Why It Matters?

Language is more than a means of communication—it is a vessel of culture, identity, and history. As fewer people actively use regional languages, valuable knowledge and traditions risk being lost.

Tinig Bicol empowers communities to preserve their language by contributing their own knowledge, recordings, and experiences. Every contribution becomes a digital seed that helps grow a richer, more comprehensive archive of the Bikol language for future generations.

## Prerequisites

- Node.js 18+
- Python 3.11+
- pip
- ffmpeg

## Project layout

```
├── frontend-nextjs/     Next.js 16 + React 19 + Tailwind CSS v4
├── backend/             FastAPI + SQLite (port 8000)
├── scraper/             Bikol audio/text data pipeline
├── Makefile             install, dev, test, build, clean
└── .env.example         shared env vars
```

## Quick start

```bash
make install
make dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

Or start each independently:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend-nextjs
npm install
npm run dev
```

## API endpoints

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

## Testing

```bash
make test
cd backend && pytest -xvs
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for Render deploy instructions.
