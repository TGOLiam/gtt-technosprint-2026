# AGENTS.md

Hackathon starter template — **Vite + React (JSX)** frontend, **FastAPI (Python)** backend.

## Layout

```
├── template/
│   ├── frontend/          Vite + React (port 5173)
│   ├── backend/           FastAPI + uvicorn (port 8000)
│   ├── Makefile           install, dev, test, build, clean
│   ├── .env.example       shared env vars
│   ├── .gitignore
│   ├── README.md          setup and dev commands
│   └── DEPLOYMENT.md      Render deploy guide
```

## Dev commands

```bash
make install    # npm install + pip install
make dev        # start both — backend in bg, frontend in fg, both die on Ctrl+C
make test       # pytest + npm test
make build      # frontend npm run build
```

Or independently:
- **Backend**: `cd backend && uvicorn app.main:app --reload --port 8000`
- **Frontend**: `cd frontend && npm install && npm run dev`
- **Test backend**: `cd backend && pytest -xvs`

## Proxy convention

`vite.config.js` proxies `/api/*` to `http://localhost:8000`. Frontend fetches `/api/health` without specifying the backend origin during development.

## Backend structure

| Path | Role |
|---|---|
| `backend/app/main.py` | FastAPI app with CORS middleware |
| `backend/app/config.py` | pydantic-settings from `.env` |
| `backend/app/routers/` | Route modules, registered via `register_routers(app)` |
| `backend/app/routers/health.py` | `GET /api/health` |
| `backend/app/models/` | Pydantic schemas |
| `backend/app/services/` | Business logic |
| `backend/tests/test_main.py` | TestClient health-check smoke test |

## Render deployment

See `DEPLOYMENT.md`. Backend as Web Service, frontend as Static Site. `Procfile` defines the start command.

## .env loading

Backend reads `.env` from the repo root via `pydantic-settings`. Frontend env vars must be prefixed with `VITE_` (Vite convention). Render dashboard env vars override the `.env` file at runtime.
