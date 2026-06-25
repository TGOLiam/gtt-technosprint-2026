# GTT: Tinig Bicol
## Preserving the Bicol Lanuage, One Word at a Time
Members:
Ebron, Pocsidio, Nadela, Serrano

## Overview

Tinig Bicol is an open, community-driven digital repository designed to preserve and promote the Bikol language. The platform allows native speakers, educators, and community members to contribute Bikol words, translations, example sentences, dialect variations, and authentic audio recordings.

By combining language preservation with collaborative knowledge sharing, Tinig Bicol aims to create a living archive of the Bikol language while making it accessible to learners, researchers, and future generations.

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

## Quick start

```bash
make install   # install both frontend and backend dependencies
make dev       # start both dev servers (backend: :8000, frontend: :5173)
```

Or start each independently:

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Frontend dev server proxies `/api/*` requests to `http://localhost:8000`.

## Project layout

```
├── frontend/          Vite + React (port 5173)
├── backend/           FastAPI + uvicorn (port 8000)
├── Makefile           install, dev, test, build, clean
├── .env.example       shared env vars template
└── DEPLOYMENT.md      Render deploy guide
```

## Testing

```bash
make test                          # both
cd backend && pytest -xvs          # backend only
cd frontend && npm test            # frontend only
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for Render deploy instructions.
