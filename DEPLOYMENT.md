# Deployment — Render

This guide deploys both services from the same GitHub repo:
- **Static Site** — frontend (Vite build output in `frontend/dist`)
- **Web Service** — backend (uvicorn via Procfile)

---

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "init"
git remote add origin <your-repo-url>
git push -u origin main
```

---

## 2. Backend — Web Service

| Setting | Value |
|---|---|
| **Build command** | `pip install -r backend/requirements.txt` |
| **Start command** | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Steps:
1. In Render Dashboard → **New +** → **Web Service**
2. Connect your GitHub repo
3. Name: `technosprint-backend`
4. Root Directory: *(blank / repo root)*
5. Build Command: `pip install -r backend/requirements.txt`
6. Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Select free plan → **Create Web Service**
8. Copy the `.onrender.com` URL — you'll need it below.

---

## 3. Frontend — Static Site

| Setting | Value |
|---|---|
| **Build command** | `cd frontend && npm install && npm run build` |
| **Publish directory** | `frontend/dist` |

Steps:
1. In Render Dashboard → **New +** → **Static Site**
2. Connect the same GitHub repo
3. Name: `technosprint-frontend`
4. Root Directory: *(blank / repo root)*
5. Build Command: `cd frontend && npm install && npm run build`
6. Publish Directory: `frontend/dist`
7. **Add environment variable**: `VITE_API_URL` = the backend URL from step 2
8. Select free plan → **Create Static Site**

---

## 4. Wire them together

| Where | What to set |
|---|---|
| **Frontend env** | `VITE_API_URL` = `https://technosprint-backend.onrender.com` |
| **Backend env** | `BACKEND_CORS_ORIGINS` = `https://technosprint-frontend.onrender.com` |

After adding the backend URL to the frontend env vars, **redeploy** the Static Site (Render → Manual Deploy → Clear build cache & deploy).

---

## Local env vs production

The template uses a single `.env` at the repo root. Render env vars override it at runtime:

```
# .env (defaults — safe to commit without secrets)
BACKEND_CORS_ORIGINS=http://localhost:5173
VITE_API_URL=http://localhost:8000
```

Render dashboard env vars take precedence. Keep secrets (API keys, DB URLs) only in Render, never in `.env`.
