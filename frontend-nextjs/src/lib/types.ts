// Types mirror the planned Supabase schema (Users / Sentences / Recordings)
// so the backend teammate can swap mock data for real API calls 1:1.

export type Region = "naga" | "albay";

export interface User {
  id: string;
  username: string;
  region: Region;
  created_at: string;
}

export interface SentenceItem {
  id: string;
  text: string;
  translation?: string;
  difficulty: "easy" | "medium" | "hard";
}

export type RecordingStatus = "pending" | "accepted" | "rejected";

export interface Recording {
  id: string;
  user_id: string;
  sentence_id: string;
  audio_url: string;
  transcript: string;
  similarity_score: number; // 0-100
  status: RecordingStatus;
  created_at: string;
}

export interface DashboardStats {
  total_recordings: number;
  native_contributors: number;
  average_quality: number; // percentage
  hours_collected: number;
}

export interface LeaderboardEntry {
  username: string;
  region: Region;
  count: number;
}

export interface Achievement {
  id: string;
  label: string;
  emoji: string;
  threshold: number;
}
