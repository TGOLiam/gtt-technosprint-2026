import {
  Achievement,
  DashboardStats,
  LeaderboardEntry,
  Recording,
  SentenceItem,
} from "./types";

// Bicolano prompt sentences — pulled straight from the project brief.
export const MOCK_SENTENCES: SentenceItem[] = [
  { id: "s1", text: "Marhay na aga.", translation: "Good morning.", difficulty: "easy" },
  { id: "s2", text: "Dios mabalos.", translation: "Thank you (formal).", difficulty: "easy" },
  { id: "s3", text: "Ano an ngaran mo?", translation: "What is your name?", difficulty: "easy" },
  { id: "s4", text: "Taga sain ka?", translation: "Where are you from?", difficulty: "easy" },
  { id: "s5", text: "Salamat.", translation: "Thanks.", difficulty: "easy" },
  { id: "s6", text: "Pwede tabi?", translation: "May I, please?", difficulty: "easy" },
  { id: "s7", text: "Makaon na kita.", translation: "Let's eat.", difficulty: "medium" },
  { id: "s8", text: "Madalagan ako.", translation: "I will run.", difficulty: "medium" },
  { id: "s9", text: "Masiram an pagkaon.", translation: "The food is delicious.", difficulty: "medium" },
  { id: "s10", text: "Mayong banggi.", translation: "Good evening.", difficulty: "easy" },
];

export const MOCK_DASHBOARD_STATS: DashboardStats = {
  total_recordings: 58,
  native_contributors: 12,
  average_quality: 97,
  hours_collected: 0.63,
};

export const MOCK_LEADERBOARD: LeaderboardEntry[] = [
  { username: "John", region: "naga", count: 22 },
  { username: "Maria", region: "albay", count: 15 },
  { username: "Pedro", region: "naga", count: 12 },
];

export const MOCK_ACHIEVEMENTS: Achievement[] = [
  { id: "a1", label: "First Recording", emoji: "🏅", threshold: 1 },
  { id: "a2", label: "10 Contributions", emoji: "🏅", threshold: 10 },
  { id: "a3", label: "50 Contributions", emoji: "🏅", threshold: 50 },
];

export const MOCK_RECORDINGS: Recording[] = [
  {
    id: "r1",
    user_id: "u1",
    sentence_id: "s1",
    audio_url: "",
    transcript: "Marhay na aga.",
    similarity_score: 98,
    status: "accepted",
    created_at: new Date().toISOString(),
  },
  {
    id: "r2",
    user_id: "u2",
    sentence_id: "s3",
    audio_url: "",
    transcript: "Ano an ngaran mo?",
    similarity_score: 95,
    status: "accepted",
    created_at: new Date().toISOString(),
  },
  {
    id: "r3",
    user_id: "u3",
    sentence_id: "s5",
    audio_url: "",
    transcript: "Salamat.",
    similarity_score: 99,
    status: "accepted",
    created_at: new Date().toISOString(),
  },
];
