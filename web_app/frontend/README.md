# TinigBicol — Frontend

Open-source platform for crowdsourcing Bicolano (Naga & Albay accent) voice
recordings, validated against Whisper speech-to-text, to build an open
speech dataset.

## Run it

```bash
npm install
npm run dev
```

Visit http://localhost:3000

## What's real vs. mocked right now

The frontend runs **fully standalone** with mock data, so you can demo it
even before the backend is wired up.

- All pages, navigation, recording UI (real mic access via `MediaRecorder`),
  and animations work for real.
- Data (sentences, dataset rows, dashboard stats, leaderboard) comes from
  `src/lib/mock-data.ts` via the functions in `src/lib/api.ts`.
- Nickname + region "login" is just `localStorage` (see `src/lib/session.ts`)
  — no real auth, which is fine for a hackathon demo.

## Wiring up the real FastAPI backend

1. Copy `.env.local.example` -> `.env.local`, set `NEXT_PUBLIC_API_URL` to
   your backend's URL.
2. In `src/lib/api.ts`, set `USE_MOCK = false`.
3. Each function in that file already has the real `fetch()` call written —
   just confirm your FastAPI routes match the shapes commented above each
   function (`/sentences`, `/recordings`, `/dashboard/stats`, `/leaderboard`,
   `/dataset/export`).
4. The `submitRecording()` function sends a `multipart/form-data` POST with
   the audio blob (`audio`), `sentence_id`, and `user_id` — expects back a
   `Recording` object with `transcript`, `similarity_score`, and `status`
   (i.e. whatever your Whisper-validation endpoint returns).

## Pages

| Route | Page |
|---|---|
| `/` | Landing page (loading screen -> hero + CTAs: Start Contributing / Dashboard / About) |
| `/select-region` | Nickname + Naga/Albay region picker |
| `/record` | Sentence display, record/stop/replay/submit, Whisper validation result |
| `/dataset` | Table of accepted recordings + export (no longer linked from nav/home, still works) |
| `/dashboard` | **Pipeline GUI** — upload an audio file, runs it through the Bikol Speech Preprocessing Pipeline (normalize -> segment -> classify), same backend logic as `run.bat`. Polls every 1.5s for progress. |
| `/about` | Problem statement, solution, tech stack |

### Pipeline GUI backend contract (`/dashboard`)

```
POST /pipeline/run     multipart: file, source_name?, source_type?, dialect?
  -> { run_id, status: "queued" }

GET  /pipeline/run/{run_id}
  -> PipelineRun (see src/lib/types.ts) — poll until status is "done"/"failed"
```

This should invoke the *same* pipeline code the CLI (`run.bat`) uses, so a
file processed through the GUI produces an identical `manifest.csv` /
`rejected.csv` / `pipeline.log` as running the CLI directly.

## Tech

Next.js (App Router) + TypeScript + Tailwind CSS v4. No shadcn/ui CLI used
(network-restricted in the build sandbox) — equivalent hand-rolled
components live in `src/components/ui/`.

## Notes / known gaps

- No real auth — fine for hackathon scope, flag if judges ask.
- Dataset export button links to `/dataset/export`, assumes backend streams
  a file (CSV/JSON/zip) — confirm response headers (`Content-Disposition`)
  on the backend side.
- Recording uses `audio/webm` via `MediaRecorder`; confirm Whisper API
  accepts webm directly, or transcode server-side if needed.
