"use client";

import { useState } from "react";
import Link from "next/link";
import { LoadingScreen } from "@/components/loading-screen";
import { Button } from "@/components/ui/button";
import { Mic, Database, Info, ArrowRight } from "lucide-react";

export default function HomePage() {
  const [loading, setLoading] = useState(true);

  return (
    <>
      {loading && <LoadingScreen onDone={() => setLoading(false)} />}

      <main className="weave-bg flex-1">
        {/* Hero */}
        <section className="mx-auto max-w-5xl px-6 pt-20 pb-16 text-center">
          <span className="inline-flex items-center gap-2 rounded-full border-2 border-maroon/20 bg-white/60 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-maroon">
            Naga &amp; Albay accents &middot; more coming soon
          </span>

          <h1 className="font-display mt-6 text-5xl font-extrabold leading-[1.05] text-ink sm:text-6xl md:text-7xl">
            Help preserve and advance the{" "}
            <span className="text-maroon">Bicolano</span> language
            <span className="text-marigold-deep">.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-soft">
            Read a sentence. Record your voice. In seconds, an open dataset
            grows — built by native speakers, for the researchers and
            AI developers building the next generation of Bicolano speech
            technology.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/select-region">
              <Button size="lg" variant="primary">
                <Mic size={20} /> Start Contributing
              </Button>
            </Link>
            <Link href="/dataset">
              <Button size="lg" variant="secondary">
                <Database size={20} /> View Dataset
              </Button>
            </Link>
            <Link href="/about">
              <Button size="lg" variant="outline">
                <Info size={20} /> About
              </Button>
            </Link>
          </div>
        </section>

        {/* Signature element: live "sentence card" preview, the heart of the product */}
        <section className="mx-auto max-w-3xl px-6 pb-20">
          <div className="rounded-3xl border-2 border-ink/10 bg-white/80 p-8 shadow-[6px_6px_0_0_rgba(107,30,35,0.12)] sm:p-10">
            <div className="flex items-center justify-between">
              <span className="font-display text-sm font-bold uppercase tracking-wide text-ink-soft">
                Sentence #1
              </span>
              <span className="rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold text-leaf">
                98% match
              </span>
            </div>
            <p className="font-display mt-4 text-3xl font-bold text-ink sm:text-4xl">
              &ldquo;Marhay na aga.&rdquo;
            </p>
            <p className="mt-2 text-sm text-ink-soft">Good morning.</p>

            <div className="mt-8 flex items-center gap-4">
              <span className="recording-pulse flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-maroon text-cream">
                <Mic size={22} />
              </span>
              <div className="flex items-end gap-1 h-8">
                {[40, 70, 45, 90, 60, 35, 80, 50, 65, 30].map((h, i) => (
                  <span
                    key={i}
                    className="w-1.5 rounded-full bg-marigold"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
              <ArrowRight className="ml-auto text-ink-soft" size={20} />
              <span className="text-sm font-semibold text-leaf">Accepted</span>
            </div>
          </div>
          <p className="mt-4 text-center text-sm text-ink-soft">
            Every recording is checked against Whisper speech-to-text before
            it joins the dataset.
          </p>
        </section>
      </main>
    </>
  );
}
