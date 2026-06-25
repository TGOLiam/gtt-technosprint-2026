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
  MOCK_RECORDINGS,
  MOCK_SENTENCES,
} from "./mock-data";
import {
  DashboardStats,
  LeaderboardEntry,
  Recording,
  Region,
  SentenceItem,
} from "./types";

const USE_MOCK = true;
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function sleep(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

// GET /sentences?region=naga|albay
export async function getSentences(region?: Region): Promise<SentenceItem[]> {
  if (USE_MOCK) {
    await sleep(300);
    return MOCK_SENTENCES;
  }
  const res = await fetch(`${API_URL}/sentences${region ? `?region=${region}` : ""}`);
  if (!res.ok) throw new Error("Failed to fetch sentences");
  return res.json();
}

// POST /recordings  (multipart: audio file + sentence_id + user_id)
// Expected response: Recording shape including transcript + similarity_score
// from the Whisper validation step.
export async function submitRecording(params: {
  sentenceId: string;
  userId: string;
  audioBlob: Blob;
}): Promise<Recording> {
  if (USE_MOCK) {
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
  }
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
}

// GET /recordings  -> recent accepted recordings for the Dataset page
export async function getRecordings(): Promise<Recording[]> {
  if (USE_MOCK) {
    await sleep(300);
    return MOCK_RECORDINGS;
  }
  const res = await fetch(`${API_URL}/recordings`);
  if (!res.ok) throw new Error("Failed to fetch recordings");
  return res.json();
}

// GET /dashboard/stats
export async function getDashboardStats(): Promise<DashboardStats> {
  if (USE_MOCK) {
    await sleep(300);
    return MOCK_DASHBOARD_STATS;
  }
  const res = await fetch(`${API_URL}/dashboard/stats`);
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  return res.json();
}

// GET /leaderboard
export async function getLeaderboard(): Promise<LeaderboardEntry[]> {
  if (USE_MOCK) {
    await sleep(300);
    return MOCK_LEADERBOARD;
  }
  const res = await fetch(`${API_URL}/leaderboard`);
  if (!res.ok) throw new Error("Failed to fetch leaderboard");
  return res.json();
}

// GET /dataset/export -> triggers file download of the dataset (CSV/JSON/zip)
export function getExportUrl(): string {
  return `${API_URL}/dataset/export`;
}
