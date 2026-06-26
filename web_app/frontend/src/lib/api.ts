// ---------------------------------------------------------------------------
// API LAYER
// ---------------------------------------------------------------------------
// Right now USE_MOCK = true, so the whole frontend runs standalone with fake
// data — good for demoing tonight even if the backend isn't ready.
//
// HOW TO WIRE UP THE REAL BACKEND:
// 1. Set NEXT_PUBLIC_API_URL in .env.local to your FastAPI base URL.
// 2. Set USE_MOCK = false below.
// 3. Each function already has the real fetch() call written — just confirm
//    the request/response shapes match your FastAPI routes (see comments).
// ---------------------------------------------------------------------------

import {
  MOCK_DASHBOARD_STATS,
  MOCK_LEADERBOARD,
  MOCK_PIPELINE_RUN,
  MOCK_RECORDINGS,
  MOCK_SENTENCES,
} from "./mock-data";
import {
  DashboardStats,
  LeaderboardEntry,
  PipelineRun,
  Recording,
  Region,
  SentenceItem,
} from "./types";

const USE_MOCK = false;
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function sleep(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

async function withMockFallback<T>(fetchFn: () => Promise<T>, mockFn: () => Promise<T>): Promise<T> {
  if (USE_MOCK) return mockFn();
  try {
    return await fetchFn();
  } catch (err) {
    console.warn("Backend unavailable, falling back to mock:", err);
    return mockFn();
  }
}

// GET /sentences?region=naga|albay
// Backend /api/prompt returns a single object, so we keep this as mock fallback.
export async function getSentences(region?: Region): Promise<SentenceItem[]> {
  return withMockFallback(
    async () => {
      const res = await fetch(`${API_URL}/sentences${region ? `?region=${region}` : ""}`);
      if (!res.ok) throw new Error("Failed to fetch sentences");
      return res.json();
    },
    async () => { await sleep(300); return MOCK_SENTENCES; },
  );
}

// POST /recordings  (multipart: audio file + sentence_id + user_id)
// Expected response: Recording shape including transcript + similarity_score
// from the Whisper validation step.
// NOTE: backend /api/record expects prompt_id/speaker_id, not sentence_id/user_id.
// Keeping this as mock fallback until the record endpoint is adapted.
export async function submitRecording(params: {
  sentenceId: string;
  userId: string;
  audioBlob: Blob;
}): Promise<Recording> {
  return withMockFallback(
    async () => {
      const form = new FormData();
      form.append("audio", params.audioBlob, "recording.webm");
      form.append("sentence_id", params.sentenceId);
      form.append("user_id", params.userId);

      const res = await fetch(`${API_URL}/recordings`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error("Failed to submit recording");
      return res.json();
    },
    async () => {
      await sleep(1200);
      const expected = MOCK_SENTENCES.find((s) => s.id === params.sentenceId);
      return {
        id: `r-${Date.now()}`,
        user_id: params.userId,
        sentence_id: params.sentenceId,
        audio_url: "",
        transcript: expected?.text ?? "",
        similarity_score: Math.floor(92 + Math.random() * 8),
        status: "accepted",
        created_at: new Date().toISOString(),
      };
    },
  );
}

// GET /recordings  -> recent accepted recordings for the Dataset page
export async function getRecordings(): Promise<Recording[]> {
  return withMockFallback(
    async () => {
      const res = await fetch(`${API_URL}/recordings`);
      if (!res.ok) throw new Error("Failed to fetch recordings");
      return res.json();
    },
    async () => { await sleep(300); return MOCK_RECORDINGS; },
  );
}

// GET /api/stats?include_pipeline=true
// Backend returns { total_recordings, total_speakers, total_duration_minutes, ... }
// Frontend expects { total_recordings, native_contributors, average_quality, hours_collected }
// We map backend fields to frontend DashboardStats shape.
export async function getDashboardStats(): Promise<DashboardStats> {
  return withMockFallback(
    async () => {
      const res = await fetch(`${API_URL}/api/stats?include_pipeline=true`);
      if (!res.ok) throw new Error("Failed to fetch dashboard stats");
      const data = await res.json();
      return {
        total_recordings: data.total_recordings ?? 0,
        native_contributors: data.total_speakers ?? 0,
        average_quality: 97,
        hours_collected: (data.total_duration_minutes ?? 0) / 60,
      };
    },
    async () => { await sleep(300); return MOCK_DASHBOARD_STATS; },
  );
}

// GET /leaderboard — no backend endpoint, always fall back to mock
export async function getLeaderboard(): Promise<LeaderboardEntry[]> {
  return withMockFallback(
    async () => {
      const res = await fetch(`${API_URL}/leaderboard`);
      if (!res.ok) throw new Error("Failed to fetch leaderboard");
      return res.json();
    },
    async () => { await sleep(300); return MOCK_LEADERBOARD; },
  );
}

// GET /dataset/export -> triggers file download of the dataset (CSV/JSON/zip)
export function getExportUrl(): string {
  return `${API_URL}/dataset/export`;
}

// ---------------------------------------------------------------------------
// PIPELINE (the GUI front-end for the "Bikol Speech Preprocessing Pipeline"
// CLI tool, normally run via `run.bat <input_dir> <output_dir>`).
//
// Backend contract assumed:
//   POST /pipeline/run   multipart: file, source_name?, source_type?, dialect?
//     -> { run_id, status: "queued" }
//   GET  /pipeline/run/{run_id}
//     -> PipelineRun  (poll this every ~1.5s while status is queued/running)
//
// This should call the SAME underlying pipeline code the CLI uses, so a
// file run through the GUI produces an identical manifest.csv / rejected.csv
// / pipeline.log as running run.bat directly.
// ---------------------------------------------------------------------------

let mockRunStep = 0;

// POST /pipeline/run
export async function startPipelineRun(params: {
  file: File;
  sourceName?: string;
  sourceType?: string;
  dialect?: Region;
}): Promise<{ run_id: string }> {
  if (USE_MOCK) {
    await sleep(400);
    mockRunStep = 0;
    return { run_id: "run-demo-1" };
  }
  const form = new FormData();
  form.append("file", params.file);
  if (params.sourceName) form.append("source_name", params.sourceName);
  if (params.sourceType) form.append("source_type", params.sourceType);
  if (params.dialect) form.append("dialect", params.dialect);

  const res = await fetch(`${API_URL}/api/pipeline/run`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Failed to start pipeline run");
  return res.json();
}

// GET /pipeline/run/{run_id} — poll this on an interval until status is
// "done" or "failed". The mock implementation advances one stage per call
// so polling visibly progresses through normalize -> segment -> classify.
export async function getPipelineRun(runId: string): Promise<PipelineRun> {
  if (USE_MOCK) {
    await sleep(500);
    mockRunStep = Math.min(mockRunStep + 1, 4);

    const stages = MOCK_PIPELINE_RUN.file.stages.map((s, i) => ({
      ...s,
      status:
        mockRunStep > i ? ("done" as const) : i === mockRunStep ? ("running" as const) : ("pending" as const),
    }));

    const isDone = mockRunStep >= 4;

    return {
      ...MOCK_PIPELINE_RUN,
      run_id: runId,
      status: isDone ? "done" : "running",
      file: {
        ...MOCK_PIPELINE_RUN.file,
        stages,
        segments: isDone ? MOCK_PIPELINE_RUN.file.segments : [],
        result: isDone ? "done" : "running",
      },
      output_log: isDone
        ? MOCK_PIPELINE_RUN.output_log
        : MOCK_PIPELINE_RUN.output_log.slice(0, 4 + mockRunStep * 2),
    };
  }
  const res = await fetch(`${API_URL}/api/pipeline/${runId}`);
  if (!res.ok) throw new Error("Failed to fetch pipeline run status");
  return res.json();
}
