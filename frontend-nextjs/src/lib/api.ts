import { DashboardStats, Recording, Region, SentenceItem } from "./types";

const USE_MOCK = false;
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// GET /api/prompt?dialect=naga|albay
export async function getSentences(region?: Region): Promise<SentenceItem[]> {
  if (USE_MOCK) {
    const { MOCK_SENTENCES } = await import("./mock-data");
    return MOCK_SENTENCES;
  }

  const params = region ? `?dialect=${region}` : "";
  const res = await fetch(`${API_URL}/api/prompt${params}`);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch sentences (${res.status}): ${text}`);
  }
  const data = await res.json();

  return [
    {
      id: data.id,
      text: data.text,
      translation: tagline(data.dialect_variant),
      difficulty: "easy",
    },
  ];
}

// POST /api/record  (multipart: audio + prompt_id + speaker_id + dialect_label)
export async function submitRecording(params: {
  sentenceId: string;
  userId: string;
  audioBlob: Blob;
  dialectLabel: Region;
}): Promise<Recording> {
  if (USE_MOCK) {
    const { MOCK_SENTENCES } = await import("./mock-data");
    await new Promise((r) => setTimeout(r, 800));
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
  form.append("prompt_id", params.sentenceId);
  form.append("speaker_id", params.userId);
  form.append("dialect_label", params.dialectLabel);
  form.append("consent_granted", "true");

  const res = await fetch(`${API_URL}/api/record`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to submit recording (${res.status}): ${text}`);
  }
  const data = await res.json();

  return {
    id: data.recording_id,
    user_id: data.speaker_id,
    sentence_id: params.sentenceId,
    audio_url: "",
    transcript: "",
    similarity_score: 95,
    status: "accepted",
    created_at: new Date().toISOString(),
  };
}

// GET /api/stats
export async function getDashboardStats(): Promise<DashboardStats> {
  if (USE_MOCK) {
    const { MOCK_DASHBOARD_STATS } = await import("./mock-data");
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_DASHBOARD_STATS;
  }

  const res = await fetch(`${API_URL}/api/stats`);
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  const data = await res.json();

  return {
    total_recordings: data.total_recordings,
    native_contributors: data.total_speakers,
    average_quality: 95,
    hours_collected: Number((data.total_duration_minutes / 60).toFixed(2)),
  };
}

// GET /api/stats (reuse for recordings)
export async function getRecordings(): Promise<Recording[]> {
  if (USE_MOCK) {
    const { MOCK_RECORDINGS } = await import("./mock-data");
    await new Promise((r) => setTimeout(r, 300));
    return MOCK_RECORDINGS;
  }
  return [];
}

// Not yet implemented on backend
export async function getLeaderboard() {
  const { MOCK_LEADERBOARD } = await import("./mock-data");
  await new Promise((r) => setTimeout(r, 300));
  return MOCK_LEADERBOARD;
}

// Not yet implemented on backend
export function getExportUrl(): string {
  return `${API_URL}/api/stats`;
}

function tagline(dialect: string): string {
  if (dialect === "naga") return "Naga / Coastal Bikol";
  if (dialect === "albay") return "Albay / Inland Bikol";
  return "Bikol";
}
