"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getPipelineRun, startPipelineRun } from "@/lib/api";
import { PipelineRun, Region } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const SESSION_KEY = "active_pipeline_run";

function saveToSession(runId: string, fileName: string) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ runId, fileName }));
  } catch {}
}

function clearSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {}
}

function loadFromSession(): { runId: string; fileName: string } | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function usePipelinePolling() {
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const safeSetRun = useCallback((r: PipelineRun | null) => {
    if (mountedRef.current) setRun(r);
  }, []);

  const safeSetError = useCallback((e: string | null) => {
    if (mountedRef.current) setError(e);
  }, []);

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
        safeSetRun(result);
        if (result.status === "done" || result.status === "failed") {
          stopPolling();
          clearSession();
        }
        return result;
      } catch {
        safeSetError("Lost connection to the pipeline while checking status.");
        stopPolling();
        return null;
      }
    },
    [stopPolling, safeSetRun, safeSetError]
  );

  const start = useCallback(
    async (params: { files: File[]; sourceName?: string; sourceType?: string; dialect?: Region }): Promise<string> => {
      safeSetError(null);
      try {
        const { run_id } = await startPipelineRun(params);
        saveToSession(run_id, String(params.files.length));
        await poll(run_id);
        intervalRef.current = setInterval(() => poll(run_id), POLL_INTERVAL_MS);
        return run_id;
      } catch {
        safeSetError("Could not start the pipeline. Check the backend connection.");
        return "";
      }
    },
    [poll, safeSetRun, safeSetError]
  );

  const resume = useCallback(
    async (runId: string) => {
      safeSetError(null);
      stopPolling();
      try {
        const result = await poll(runId);
        if (result && (result.status === "running" || result.status === "queued")) {
          intervalRef.current = setInterval(() => poll(runId), POLL_INTERVAL_MS);
        }
      } catch {
        safeSetError("Could not restore pipeline session.");
      }
    },
    [poll, stopPolling, safeSetError]
  );

  const resumeFromSession = useCallback((): string | null => {
    const session = loadFromSession();
    if (session) {
      resume(session.runId);
      return session.runId;
    }
    return null;
  }, [resume]);

  const reset = useCallback(() => {
    stopPolling();
    safeSetRun(null);
    safeSetError(null);
    clearSession();
  }, [stopPolling, safeSetRun, safeSetError]);

  useEffect(() => stopPolling, [stopPolling]);

  return { run, error, start, resume, resumeFromSession, reset, isRunning: run?.status === "running" || run?.status === "queued" };
}
