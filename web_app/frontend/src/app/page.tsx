"use client";

import { useState } from "react";
import Link from "next/link";
import { LoadingScreen } from "@/components/loading-screen";
import { Button } from "@/components/ui/button";
import { Mic, LayoutDashboard, Info, ArrowRight } from "lucide-react";

export default function HomePage() {
  const [loading, setLoading] = useState(true);

  return (
    <>
      {loading && <LoadingScreen onDone={() => setLoading(false)} />}

      <main className="weave-bg flex-1">
        {/* Hero */}
        <section className="mx-auto max-w-5xl px-6 pt-20 pb-16 text-center">
          <span className="inline-flex items-center gap-2 rounded-full border-2 border-maroon/20 bg-white/60 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-maroon">
             more coming soon
          </span>

          <h1 className="font-display mt-6 text-5xl font-extrabold leading-[1.05] text-ink sm:text-6xl md:text-7xl">
            Help preserve and advance the{" "}
            <span className="text-maroon">Bicolano</span> language
            <span className="text-marigold-deep">.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-soft">
            A speech data preparation tool that cleans, validates, and structures raw Bikol audio into high-quality datasets for future speech recognition and language technology projects. 

          </p>


          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/dashboard">
              <Button size="lg" variant="secondary">
                <LayoutDashboard size={20} /> Dashboard
              </Button>
            </Link>

            <Link href="/select-region">
              <Button size="lg" variant="primary">
                <Mic size={20} /> Recording
              </Button>
            </Link>

            <Link href="/about">
              <Button size="lg" variant="outline">
                <Info size={20} /> About
              </Button>
            </Link>
          </div>



        </section>

        
      </main>
    </>
  );
}
