"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { NavBar } from "@/components/nav-bar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ValidationResult } from "@/components/validation-result";
import { useRecorder } from "@/lib/use-recorder";
import { getSession, Session } from "@/lib/session";
import { getSentences, submitRecording } from "@/lib/api";
import { Recording, SentenceItem } from "@/lib/types";
import { Mic, Square, Play, Upload, SkipForward, MapPin } from "lucide-react";

export default function RecordPage() {
  const router = useRouter();
  const [session] = useState<Session | null>(() => getSession());
  const [sentences, setSentences] = useState<SentenceItem[]>([]);
  const [index, setIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<Recording | null>(null);

  const recorder = useRecorder();
  const current = sentences[index];

  useEffect(() => {
    if (!session) {
      router.replace("/select-region");
      return;
    }
    getSentences(session.region).then(setSentences);
  }, [router, session]);

  const progressLabel = useMemo(
    () => `Sentence ${index + 1} of ${sentences.length || "…"}`,
    [index, sentences.length]
  );

  async function handleSubmit() {
    if (!recorder.audioBlob || !current || !session) return;
    setSubmitting(true);
    try {
      const rec = await submitRecording({
        sentenceId: current.id,
        userId: session.id,
        audioBlob: recorder.audioBlob,
      });
      setResult(rec);
    } finally {
      setSubmitting(false);
    }
  }

  function handleNext() {
    recorder.reset();
    setResult(null);
    setIndex((i) => (i + 1) % sentences.length);
  }

  if (!session || !current) {
    return (
      <>
        <NavBar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-ink-soft">Loading sentences…</p>
        </main>
      </>
    );
  }

  return (
    <>
      <NavBar />
      <main className="weave-bg flex-1 px-6 py-12">
        <div className="mx-auto max-w-xl">
          <div className="flex items-center justify-between">
            <Badge tone="marigold">{progressLabel}</Badge>
            <Badge tone="neutral">
              <MapPin size={12} /> {session.username} &middot; {session.region}
            </Badge>
          </div>

          <Card className="mt-6 text-center">
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
              Read this sentence aloud
            </p>
            <p className="font-display mt-3 text-3xl font-bold text-ink sm:text-4xl">
              &ldquo;{current.text}&rdquo;
            </p>
            {current.translation && (
              <p className="mt-2 text-sm text-ink-soft">{current.translation}</p>
            )}

            {/* Recording controls */}
            <div className="mt-8 flex flex-col items-center gap-4">
              {recorder.status !== "stopped" && (
                <button
                  onClick={recorder.status === "recording" ? recorder.stop : recorder.start}
                  className={`flex h-20 w-20 items-center justify-center rounded-full text-cream transition-colors ${
                    recorder.status === "recording"
                      ? "recording-pulse bg-maroon"
                      : "bg-maroon hover:bg-maroon-light"
                  }`}
                  aria-label={recorder.status === "recording" ? "Stop recording" : "Start recording"}
                >
                  {recorder.status === "recording" ? <Square size={26} /> : <Mic size={28} />}
                </button>
              )}

              {recorder.status === "recording" && (
                <p className="text-sm font-medium text-maroon">Recording… tap to stop</p>
              )}

              {recorder.error && (
                <p className="text-sm font-medium text-maroon">{recorder.error}</p>
              )}

              {recorder.status === "stopped" && recorder.audioUrl && !result && (
                <div className="w-full space-y-4">
                  <audio src={recorder.audioUrl} controls className="w-full" />
                  <div className="flex justify-center gap-3">
                    <Button variant="outline" size="sm" onClick={recorder.reset}>
                      <Play size={16} /> Re-record
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleSubmit}
                      disabled={submitting}
                    >
                      <Upload size={16} />
                      {submitting ? "Checking with Whisper…" : "Submit"}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {result && (
            <div className="mt-6 space-y-4">
              <ValidationResult
                expected={current.text}
                transcript={result.transcript}
                score={result.similarity_score}
                accepted={result.status === "accepted"}
              />
              <Button onClick={handleNext} size="lg" className="w-full">
                <SkipForward size={18} /> Next sentence
              </Button>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
