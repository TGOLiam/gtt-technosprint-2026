"use client";

import { useEffect, useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getRecordings, getExportUrl } from "@/lib/api";
import { MOCK_SENTENCES } from "@/lib/mock-data";
import { Recording } from "@/lib/types";
import { CheckCircle2, Download, Loader2 } from "lucide-react";

export default function DatasetPage() {
  const [recordings, setRecordings] = useState<Recording[] | null>(null);

  useEffect(() => {
    getRecordings().then(setRecordings);
  }, []);

  function sentenceText(id: string) {
    return MOCK_SENTENCES.find((s) => s.id === id)?.text ?? "—";
  }

  return (
    <>
      <NavBar />
      <main className="weave-bg flex-1 px-6 py-12">
        <div className="mx-auto max-w-3xl">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl font-extrabold text-ink">
                The dataset, so far
              </h1>
              <p className="mt-1 text-ink-soft">
                Every accepted recording, validated against Whisper
                speech-to-text.
              </p>
            </div>
            <a href={getExportUrl()} target="_blank" rel="noreferrer">
              <Button variant="outline" size="sm">
                <Download size={16} /> Export dataset
              </Button>
            </a>
          </div>

          <Card className="mt-8 p-0 overflow-hidden">
            {!recordings ? (
              <div className="flex items-center justify-center gap-2 py-12 text-ink-soft">
                <Loader2 className="animate-spin" size={18} /> Loading dataset…
              </div>
            ) : (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b-2 border-ink/10 bg-cream-deep/60">
                    <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                      Sentence
                    </th>
                    <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                      Match
                    </th>
                    <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recordings.map((rec, i) => (
                    <tr
                      key={rec.id}
                      className={i % 2 === 0 ? "bg-white/40" : "bg-transparent"}
                    >
                      <td className="px-6 py-4 font-display font-semibold text-ink">
                        {sentenceText(rec.sentence_id)}
                      </td>
                      <td className="px-6 py-4 text-ink-soft">
                        {rec.similarity_score}%
                      </td>
                      <td className="px-6 py-4">
                        {rec.status === "accepted" ? (
                          <Badge tone="leaf">
                            <CheckCircle2 size={12} /> Accepted
                          </Badge>
                        ) : (
                          <Badge tone="neutral">{rec.status}</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </div>
      </main>
    </>
  );
}
