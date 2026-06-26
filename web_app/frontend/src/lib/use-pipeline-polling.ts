"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getPipelineRun, startPipelineRun } from "@/lib/api";
import { PipelineRun, Region } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;

export function usePipelinePolling() {
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const poll = useCallback(
    async (runId: string) => {
      try {
        const result = await getPipelineRun(runId);
        setRun(result);
        if (result.status === "done" || result.status === "failed") {
          stopPolling();
        }
      } catch {
        setError("Lost connection to the pipeline while checking status.");
        stopPolling();
      }
    },
    [stopPolling]
  );

  const start = useCallback(
    async (params: { file: File; sourceName?: string; sourceType?: string; dialect?: Region }) => {
      setError(null);
      setRun(null);
      try {
        const { run_id } = await startPipelineRun(params);
        await poll(run_id);
        intervalRef.current = setInterval(() => poll(run_id), POLL_INTERVAL_MS);
      } catch {
        setError("Could not start the pipeline. Check the backend connection.");
      }
    },
    [poll]
  );

  const reset = useCallback(() => {
    stopPolling();
    setRun(null);
    setError(null);
  }, [stopPolling]);

  useEffect(() => stopPolling, [stopPolling]);

  return { run, error, start, reset, isRunning: run?.status === "running" || run?.status === "queued" };
}
