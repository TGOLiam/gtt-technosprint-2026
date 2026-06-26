"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { NavBar } from "@/components/nav-bar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePipelinePolling } from "@/lib/use-pipeline-polling";
import { Region } from "@/lib/types";
import {
  Upload,
  Download,
  CheckCircle2,
  XCircle,
  Loader2,
  Circle,
  FileAudio,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getPipelineDownloadUrl } from "@/lib/api";

const REGIONS: Region[] = ["naga", "albay"];

function StageIcon({ status }: { status: string }) {
  if (status === "done") return <CheckCircle2 size={14} className="text-leaf" />;
  if (status === "running")
    return <Loader2 size={14} className="animate-spin text-marigold-deep" />;
  if (status === "failed") return <XCircle size={14} className="text-maroon" />;
  return <Circle size={14} className="text-ink-soft/40" />;
}

export default function DashboardPage() {
  const { run, error, start, resume, resumeFromSession, reset, isRunning } = usePipelinePolling();
  const router = useRouter();
  const searchParams = useSearchParams();
  const runIdFromUrl = searchParams.get("run_id");
  const hasResumed = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [sourceName, setSourceName] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [dialect, setDialect] = useState<Region>("albay");
  const [fileNames, setFileNames] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [submitted, setSubmitted] = useState(false);

  // Resume from sessionStorage first (survives page navigation),
  // then fall back to URL query param (for links / bookmarks).
  useEffect(() => {
    if (hasResumed.current) return;
    hasResumed.current = true;

    const fromSession = resumeFromSession();
    if (!fromSession && runIdFromUrl) {
      resume(runIdFromUrl);
    }
  }, [runIdFromUrl, resume, resumeFromSession]);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const incoming = Array.from(files);
    const existingNames = new Set(selectedFiles.map(f => f.name));
    const newFiles = incoming.filter(f => !existingNames.has(f.name));
    if (newFiles.length === 0) return;
    setSelectedFiles(prev => [...prev, ...newFiles]);
    setFileNames(prev => [...prev, ...newFiles.map(f => f.name)]);
    setSubmitted(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleStart() {
    if (selectedFiles.length === 0) return;
    hasResumed.current = true;
    const runId = await start({ files: selectedFiles, sourceName, sourceType, dialect });
    if (runId) {
      router.push(`/dashboard?run_id=${runId}`);
    }
  }

  function handleSubmit() {
    if (selectedFiles.length === 0) return;
    setSubmitted(true);
  }

  return (
    <>
      <NavBar />
      <main className="weave-bg flex-1 px-6 py-10">
        <div className="mx-auto max-w-6xl">
          <h1 className="font-display text-3xl font-extrabold text-ink">
            Dashboard
          </h1>
          <p className="mt-1 text-ink-soft">
            Run the Bikol speech preprocessing pipeline on an audio file —
            normalize, segment, and classify, same as the CLI.
          </p>

          <div className="mt-8 grid gap-6 lg:grid-cols-[320px_1fr]">
            {/* Sidebar */}
            <div className="space-y-6">
              <Card>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="audio/*,.m4a,.wav,.mp3"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isRunning}
                  className="w-full"
                  size="sm"
                >
                  <Upload size={16} /> {fileNames.length > 0 ? "Add more files" : "Upload audio files"}
                </Button>

                <div className="mt-5 space-y-3">
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                      Source Name
                    </label>
                    <input
                      value={sourceName}
                      onChange={(e) => setSourceName(e.target.value)}
                      placeholder="e.g. learnbicol"
                      disabled={isRunning}
                      className="mt-1 w-full rounded-lg border-2 border-ink/10 bg-white px-3 py-1.5 text-sm outline-none focus:border-maroon disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                      Source Type
                    </label>
                    <input
                      value={sourceType}
                      onChange={(e) => setSourceType(e.target.value)}
                      placeholder="e.g. dictionary"
                      disabled={isRunning}
                      className="mt-1 w-full rounded-lg border-2 border-ink/10 bg-white px-3 py-1.5 text-sm outline-none focus:border-maroon disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                      Label Dialect
                    </label>
                    <div className="mt-1 flex gap-2">
                      {REGIONS.map((r) => (
                        <button
                          key={r}
                          type="button"
                          disabled={isRunning}
                          onClick={() => setDialect(r)}
                          className={cn(
                            "flex-1 rounded-lg border-2 px-3 py-1.5 text-sm font-medium capitalize transition-colors disabled:opacity-50",
                            dialect === r
                              ? "border-maroon bg-maroon/5 text-maroon"
                              : "border-ink/10 bg-white text-ink-soft"
                          )}
                        >
                          {r}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {fileNames.length > 0 && (
                  <>
                    <div className="mt-5 border-t-2 border-ink/10 pt-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
                        File Details
                      </p>
                      <dl className="mt-2 space-y-1 text-sm">
                        <div className="flex justify-between gap-2">
                          <dt className="text-ink-soft">Files</dt>
                          <dd className="truncate font-medium text-ink">{fileNames.length} file{fileNames.length !== 1 ? 's' : ''}</dd>
                        </div>
                        {fileNames.map((name, i) => (
                          <div key={i} className="flex items-center justify-between gap-2 pl-2">
                            <dt className="truncate text-ink-soft">{name}</dt>
                            {!submitted && !isRunning && (
                              <button
                                onClick={() => {
                                  setSelectedFiles(prev => prev.filter((_, idx) => idx !== i));
                                  setFileNames(prev => prev.filter((_, idx) => idx !== i));
                                }}
                                className="text-xs text-maroon hover:underline"
                              >
                                remove
                              </button>
                            )}
                          </div>
                        ))}
                        <div className="flex justify-between gap-2">
                          <dt className="text-ink-soft">Source Name</dt>
                          <dd className="font-medium text-ink">{sourceName || "—"}</dd>
                        </div>
                        <div className="flex justify-between gap-2">
                          <dt className="text-ink-soft">Source Type</dt>
                          <dd className="font-medium text-ink">{sourceType || "—"}</dd>
                        </div>
                        <div className="flex justify-between gap-2">
                          <dt className="text-ink-soft">Label Dialect</dt>
                          <dd className="font-medium capitalize text-ink">{dialect}</dd>
                        </div>
                      </dl>
                    </div>
                    {!submitted ? (
                      <Button
                        onClick={handleSubmit}
                        disabled={selectedFiles.length === 0}
                        className="mt-4 w-full"
                        size="sm"
                      >
                        Submit
                      </Button>
                    ) : (
                      <p className="mt-4 text-center text-sm font-medium text-leaf">
                        ✓ Files ready
                      </p>
                    )}
                  </>
                )}
              </Card>

              {run && (
                <Card>
                  <p className="font-display text-sm font-bold text-ink">Summary</p>
                  <dl className="mt-3 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-ink-soft">Normalization</dt>
                      <dd className="font-medium capitalize text-ink">
                        {run.summary.normalization}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-soft">Segment</dt>
                      <dd className="text-right font-medium text-ink">
                        {run.summary.segment_files} file
                        <br />
                        {run.summary.segment_count} segments
                        <br />
                        {run.summary.segment_duration_s.toFixed(1)}s total
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-soft">Classify</dt>
                      <dd className="text-right font-medium text-ink">
                        {run.summary.classify_retained} retained
                        <br />
                        {run.summary.classify_rejected} rejected
                      </dd>
                    </div>
                    {Object.keys(run.summary.rejection_reasons).length > 0 && (
                      <div className="flex justify-between">
                        <dt className="text-ink-soft">Rejections</dt>
                        <dd className="text-right font-medium text-ink">
                          {Object.entries(run.summary.rejection_reasons).map(
                            ([reason, count]) => (
                              <div key={reason}>
                                {reason}: {count}
                              </div>
                            )
                          )}
                        </dd>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <dt className="text-ink-soft">Dialect</dt>
                      <dd className="font-medium capitalize text-ink">
                        {run.summary.dialect}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-soft">Run Time</dt>
                      <dd className="font-medium text-ink">
                        {run.summary.run_time_s.toFixed(1)}s
                      </dd>
                    </div>
                  </dl>
                </Card>
              )}
            </div>

            {/* Main panel */}
            <div className="space-y-6">
              <Card>
                <h2 className="font-display text-lg font-bold text-ink">
                  Pipeline Overview
                </h2>

                {!run ? (
                  fileNames.length > 0 ? (
                    <>
                      <div className="mt-4 overflow-x-auto">
                        <table className="w-full text-left text-sm">
                          <thead>
                            <tr className="border-b-2 border-ink/10 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                              <th className="py-2 pr-4">File</th>
                              <th className="py-2 pr-4">Normalize</th>
                              <th className="py-2 pr-4">Segment</th>
                              <th className="py-2 pr-4">Classify</th>
                              <th className="py-2">Result</th>
                            </tr>
                          </thead>
                          <tbody>
                            {fileNames.map((name, i) => (
                              <tr key={i} className="border-b border-ink/5 align-top">
                                <td className="py-3 pr-4 font-medium text-ink">
                                  [{i+1}/{fileNames.length}] — {name}
                                </td>
                                {["normalize", "segment", "classify"].map((s) => (
                                  <td key={s} className="py-3 pr-4">
                                    <span className="inline-flex items-center gap-1.5">
                                      <Circle size={14} className="text-ink-soft/40" />
                                      <span className="capitalize text-ink-soft">pending</span>
                                    </span>
                                  </td>
                                ))}
                                <td className="py-3">
                                  <Badge tone="marigold">Ready</Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="mt-4 flex items-center gap-3 border-t-2 border-ink/10 pt-4">
                        <Button onClick={handleStart} disabled={selectedFiles.length === 0} size="sm">
                          Start
                        </Button>
                        <Button disabled size="sm">
                          <Download size={16} /> Download Output (zip)
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="mt-8 flex flex-col items-center gap-2 py-10 text-center text-ink-soft">
                      <FileAudio size={32} className="opacity-40" />
                      <p className="text-sm">
                        Upload an audio file to run it through the pipeline.
                      </p>
                    </div>
                  )
                ) : (
                  <>
                    <div className="mt-4 overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="border-b-2 border-ink/10 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                            <th className="py-2 pr-4">File</th>
                            <th className="py-2 pr-4">Normalize</th>
                            <th className="py-2 pr-4">Segment</th>
                            <th className="py-2 pr-4">Classify</th>
                            <th className="py-2">Result</th>
                          </tr>
                        </thead>
                        <tbody>
                          {run.files.map((file, i) => (
                            <tr key={i} className="border-b border-ink/5 align-top">
                              <td className="py-3 pr-4 font-medium text-ink">
                                [{i+1}/{run.files.length}] — {file.file_name}
                              </td>
                              {file.stages.map((stage) => (
                                <td key={stage.name} className="py-3 pr-4">
                                  <span className="inline-flex items-center gap-1.5">
                                    <StageIcon status={stage.status} />
                                    <span className="capitalize text-ink-soft">
                                      {stage.status}
                                    </span>
                                  </span>
                                </td>
                              ))}
                              <td className="py-3">
                                {run.status === "done" ? (
                                  <Badge tone="leaf">Done</Badge>
                                ) : run.status === "failed" ? (
                                  <Badge tone="maroon">Failed</Badge>
                                ) : (
                                  <Badge tone="marigold">Running</Badge>
                                )}
                              </td>
                            </tr>
                          ))}

                          {run.files.some(f => f.segments.length > 0) && run.files.map((file, fi) =>
                            file.segments.length > 0 && (
                              <tr key={`segs-${fi}`}>
                                <td colSpan={5} className="py-2">
                                  <div className="space-y-1.5 pl-2">
                                    {file.segments.map((seg, si) => (
                                      <div
                                        key={si}
                                        className="flex items-center gap-2 text-sm"
                                      >
                                        {seg.status === "kept" ? (
                                          <CheckCircle2
                                            size={14}
                                            className="text-leaf"
                                          />
                                        ) : (
                                          <XCircle size={14} className="text-maroon" />
                                        )}
                                        <span className="font-mono text-ink-soft">
                                          {seg.label}
                                        </span>
                                        <span className="text-ink-soft/60">Done</span>
                                      </div>
                                    ))}
                                  </div>
                                </td>
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    </div>
                    <div className="mt-4 flex items-center gap-3 border-t-2 border-ink/10 pt-4">
                      <Button
                        onClick={handleStart}
                        disabled={isRunning || selectedFiles.length === 0}
                        size="sm"
                      >
                        Start
                      </Button>
                      <a
                        href={run.status === "done" ? getPipelineDownloadUrl(run.run_id) : undefined}
                      >
                        <Button
                          disabled={run.status !== "done"}
                          size="sm"
                        >
                          <Download size={16} /> Download Output (zip)
                        </Button>
                      </a>
                    </div>
                  </>
                )}
              </Card>

              <Card>
                <h2 className="font-display text-sm font-bold text-ink">Output</h2>
                <pre className="mt-3 max-h-72 overflow-y-auto rounded-xl bg-ink/95 p-4 text-xs leading-relaxed text-marigold/90">
{run?.output_log.join("\n") ?? "Waiting for a file to process…"}
                </pre>
              </Card>

              {error && (
                <p className="text-sm font-medium text-maroon">{error}</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
