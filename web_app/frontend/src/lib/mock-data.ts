import {
  Achievement,
  DashboardStats,
  LeaderboardEntry,
  PipelineRun,
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

// Mirrors the actual CLI sample output for `run.bat testing/test_input testing/test_output`
// (1 input file -> nba.m4a, 3 segments, 2 kept / 1 rejected as not_ph_language).
export const MOCK_PIPELINE_RUN: PipelineRun = {
  run_id: "run-demo-1",
  status: "done",
  file: {
    file_name: "nba.m4a",
    source_name: "XXX",
    source_type: "XXX",
    label_dialect: "albay",
    stages: [
      { name: "normalize", status: "done" },
      { name: "segment", status: "done" },
      { name: "classify", status: "done" },
    ],
    segments: [
      { label: "tgl 1.000s", status: "kept", duration_s: 1.0 },
      { label: "tgl 0.955s", status: "kept", duration_s: 0.955 },
      { label: "sum 0.761s", status: "rejected", duration_s: 0.761 },
    ],
    result: "done",
  },
  summary: {
    normalization: "successful",
    segment_files: 1,
    segment_count: 3,
    segment_duration_s: 29.0,
    classify_retained: 2,
    classify_rejected: 1,
    rejection_reasons: { not_ph_language: 1 },
    dialect: "albay",
    run_time_s: 53.0,
  },
  output_log: [
    "==========================================",
    "  Bikol Speech Preprocessing Pipeline",
    "==========================================",
    "",
    "Input files: 1",
    "  Stage 1 (normalize):  1 ok, 0 failed",
    "  Stage 2 (segment):    3 segments",
    "  Stage 3 (classify):   2 kept, 1 rejected",
    "    Reject reasons:",
    "      not_ph_language : 1",
    "",
    "Output:",
    "  test_output/audio/      : 2 segments",
    "  test_output/rejected/   : 1 segments",
    "  test_output/manifest.csv: 2 rows",
    "  test_output/rejected.csv: 1 rows",
    "  test_output/pipeline.log: 734 bytes",
    "",
    "Done.",
  ],
  output_paths: {
    audio_dir: "test_output/audio/",
    rejected_dir: "test_output/rejected/",
    manifest_csv: "test_output/manifest.csv",
    rejected_csv: "test_output/rejected.csv",
    pipeline_log: "test_output/pipeline.log",
  },
};
