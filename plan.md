# Project Plan — TinigBicol

## Artifact

**Bikol Speech Preprocessing Pipeline** — a reproducible, open-source tool that
transforms raw labeled media into validated, structured Bikol dialect speech
data. Input: a directory of audio/video files + a `manifest.yml`. Output:
16kHz mono WAV segments with Bikol language validation + structured CSVs.

## Tech Stack

### Web App (`web_app/`)
| Layer | Choice |
|---|---|
| Frontend | Next.js + TypeScript + Tailwind CSS v4 |
| Backend | FastAPI + SQLite |
| Audio handing | ffmpeg (server-side conversion) |
| Prompt data | Static `prompts.csv` shipped with the backend |

### Pipeline (`pipeline/`)
| Stage | Tool |
|---|---|
| Normalize | ffmpeg |
| Segment | ffmpeg `-segment_time` (hard cut) |
| Classify | `facebook/mms-lid-256` via HuggingFace transformers |

### Deployment
| Component | Platform |
|---|---|
| Backend | Render (Web Service) |
| Frontend | Vercel |
| Pipeline | Local/CLI only |

## What's NOT in Scope
- Supabase / external database
- Authentication / user accounts
- Payments
- Analytics
- ML model training or fine-tuning
- Streaming audio input
- Transcription / ASR
