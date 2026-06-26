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
            An open language depository for all — starting with Bicol.
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

              TinigBicol is a community-powered platform that helps preserve and advance the Bicolano language 
              by collecting high-quality voice recordings from native speakers. Every contribution is automatically
               processed through our speech preprocessing pipeline, where audio is normalized, segmented, and 
               language-validated before being transformed into structured datasets. In addition, our dashboard 
               allows users to upload audio files directly and process them through the same pipeline, functioning 
               as a data cleaning tool for preparing speech data. By making speech data collection and processing 
               simple and accessible, TinigBicol empowers researchers, educators, and AI developers to build the 
               first open-source Bicolano speech resources for future language technologies.

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
                "TypeScript",
                "Python",
                "FFmpeg",
                "MMS-LID-256",
                
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
