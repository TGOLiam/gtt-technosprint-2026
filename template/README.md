# Technosprint 2026

Hackathon starter template with **Vite + React** (JSX) frontend and **FastAPI** Python backend.

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
