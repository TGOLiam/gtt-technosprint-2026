import { NavBar } from "@/components/nav-bar";
import { Card } from "@/components/ui/card";
import { Languages, Database, Cpu } from "lucide-react";

export default function AboutPage() {
  return (
    <>
      <NavBar />
      <main className="weave-bg flex-1 px-6 py-12">
        <div className="mx-auto max-w-2xl">
          <h1 className="font-display text-3xl font-extrabold text-ink">
            About TinigBicol
          </h1>
          <p className="mt-1 text-ink-soft">
            An open language depository for all — starting with Bikol.
          </p>

          <Card className="mt-8">
            <h2 className="font-display flex items-center gap-2 text-lg font-bold text-ink">
              <Languages size={18} className="text-maroon" /> The problem
            </h2>
            <p className="mt-3 text-ink-soft leading-relaxed">
              Bicolano is one of the most widely spoken languages in the
              Philippines, yet there are very few high-quality, publicly
              available speech datasets for it. That makes it hard for
              researchers and developers to build AI systems that truly
              understand and support the language.
            </p>
          </Card>

          <Card className="mt-6">
            <h2 className="font-display flex items-center gap-2 text-lg font-bold text-ink">
              <Database size={18} className="text-maroon" /> Our solution
            </h2>
            <p className="mt-3 text-ink-soft leading-relaxed">
              TinigBicol is an open-source platform where native Bicolano
              speakers contribute voice recordings by reading prompted
              sentences. Each recording is automatically validated against
              Whisper speech-to-text, then stored in a structured, open
              dataset that researchers can use to train speech AI models —
              starting with the Naga (western) and Albay (eastern) accents.
            </p>
          </Card>

          <Card className="mt-6">
            <h2 className="font-display flex items-center gap-2 text-lg font-bold text-ink">
              <Cpu size={18} className="text-maroon" /> Built with
            </h2>
            <div className="mt-4 flex flex-wrap gap-2 text-sm text-ink-soft">
              {[
                "Next.js",
                "Tailwind CSS",
                "FastAPI",
                "Supabase",
                "Whisper API",
                "Vercel",
                "Render",
              ].map((tech) => (
                <span
                  key={tech}
                  className="rounded-full bg-ink/5 px-3 py-1.5 font-medium"
                >
                  {tech}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </>
  );
}
