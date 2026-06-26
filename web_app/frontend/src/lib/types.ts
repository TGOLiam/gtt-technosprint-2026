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

// ---------------------------------------------------------------------------
// Pipeline types — modeled on the "Bikol Speech Preprocessing Pipeline" CLI
// (run.bat <input_dir> <output_dir>), which runs 3 stages per file:
//   Stage 1: normalize
//   Stage 2: segment
//   Stage 3: classify (language ID model, kept vs rejected per segment)
// and writes manifest.csv / rejected.csv / pipeline.log to the output dir.
// ---------------------------------------------------------------------------

export type StageStatus = "pending" | "running" | "done" | "failed";

export interface SegmentResult {
  label: string; // e.g. "tgl 1.000s", "sum 0.761s"
  status: "kept" | "rejected";
  duration_s: number;
}

export interface PipelineStageResult {
  name: "normalize" | "segment" | "classify";
  status: StageStatus;
}

export interface PipelineFileResult {
  file_name: string; // e.g. "nba.m4a"
  source_name?: string;
  source_type?: string;
  label_dialect?: Region | string;
  stages: PipelineStageResult[];
  segments: SegmentResult[];
  result: StageStatus;
}

export interface PipelineSummary {
  normalization: "successful" | "failed" | "pending";
  segment_files: number;
  segment_count: number;
  segment_duration_s: number;
  classify_retained: number;
  classify_rejected: number;
  rejection_reasons: Record<string, number>; // e.g. { not_ph_language: 1 }
  dialect: Region | string;
  run_time_s: number;
}

export type PipelineRunStatus = "idle" | "queued" | "running" | "done" | "failed";

export interface PipelineRun {
  run_id: string;
  status: PipelineRunStatus;
  files: PipelineFileResult[];
  summary: PipelineSummary;
  output_log: string[]; // tailed lines from pipeline.log
  output_paths?: {
    audio_dir: string;
    rejected_dir: string;
    manifest_csv: string;
    rejected_csv: string;
    pipeline_log: string;
  };
}
