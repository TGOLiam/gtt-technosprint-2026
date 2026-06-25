"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { NavBar } from "@/components/nav-bar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { createSession } from "@/lib/session";
import { Region } from "@/lib/types";
import { MapPin } from "lucide-react";

const REGIONS: { id: Region; label: string; note: string }[] = [
  { id: "naga", label: "Naga", note: "Western Bicol accent" },
  { id: "albay", label: "Albay", note: "Eastern Bicol accent" },
];

export default function SelectRegionPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [region, setRegion] = useState<Region | null>(null);
  const [error, setError] = useState("");

  function handleContinue() {
    if (!username.trim()) {
      setError("Pakisulat an saimong nickname — please enter a nickname.");
      return;
    }
    if (!region) {
      setError("Pili nin rehiyon — please choose a region.");
      return;
    }
    createSession(username.trim(), region);
    router.push("/record");
  }

  return (
    <>
      <NavBar />
      <main className="weave-bg flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-md">
          <h1 className="font-display text-3xl font-extrabold text-ink text-center">
            Iyo ka taga sain?
          </h1>
          <p className="mt-2 text-center text-ink-soft">
            Tell us your nickname and your home region so we can tag your
            recordings by accent.
          </p>

          <div className="mt-8 space-y-2">
            <label htmlFor="username" className="text-sm font-semibold text-ink">
              Nickname
            </label>
            <input
              id="username"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                setError("");
              }}
              placeholder="e.g. Marites22"
              className="w-full rounded-xl border-2 border-ink/15 bg-white px-4 py-3 text-ink placeholder:text-ink-soft/50 outline-none focus:border-maroon"
            />
          </div>

          <div className="mt-6 space-y-2">
            <label className="text-sm font-semibold text-ink">Region</label>
            <div className="grid grid-cols-2 gap-3">
              {REGIONS.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => {
                    setRegion(r.id);
                    setError("");
                  }}
                  className={cn(
                    "flex flex-col items-start gap-1 rounded-xl border-2 px-4 py-3 text-left transition-colors",
                    region === r.id
                      ? "border-maroon bg-maroon/5"
                      : "border-ink/15 bg-white hover:border-ink/30"
                  )}
                >
                  <span className="flex items-center gap-1.5 font-display font-bold text-ink">
                    <MapPin size={15} className="text-maroon" />
                    {r.label}
                  </span>
                  <span className="text-xs text-ink-soft">{r.note}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Future languages, greyed out per the brief */}
          <div className="mt-6 space-y-2">
            <label className="text-sm font-semibold text-ink-soft">
              Language
            </label>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-marigold/20 px-3 py-1.5 text-xs font-semibold text-marigold-deep">
                ✔ Bicolano
              </span>
              {["Kapampangan", "Cebuano", "Ilocano"].map((lang) => (
                <span
                  key={lang}
                  className="cursor-not-allowed rounded-full bg-ink/5 px-3 py-1.5 text-xs font-medium text-ink-soft/50"
                >
                  {lang} — soon
                </span>
              ))}
            </div>
          </div>

          {error && (
            <p className="mt-4 text-sm font-medium text-maroon">{error}</p>
          )}

          <Button onClick={handleContinue} size="lg" className="mt-8 w-full">
            Continue
          </Button>
        </div>
      </main>
    </>
  );
}
