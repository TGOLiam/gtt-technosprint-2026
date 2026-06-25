"use client";

import { useEffect, useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { Card, StatCard } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDashboardStats, getLeaderboard } from "@/lib/api";
import { MOCK_ACHIEVEMENTS } from "@/lib/mock-data";
import { DashboardStats, LeaderboardEntry } from "@/lib/types";
import { Loader2, MapPin, Trophy } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[] | null>(null);

  useEffect(() => {
    getDashboardStats().then(setStats);
    getLeaderboard().then(setLeaderboard);
  }, []);

  return (
    <>
      <NavBar />
      <main className="weave-bg flex-1 px-6 py-12">
        <div className="mx-auto max-w-4xl">
          <h1 className="font-display text-3xl font-extrabold text-ink">
            Dashboard
          </h1>
          <p className="mt-1 text-ink-soft">
            How the dataset is growing, at a glance.
          </p>

          {/* Stat cards */}
          <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {!stats ? (
              <div className="col-span-4 flex items-center justify-center gap-2 py-8 text-ink-soft">
                <Loader2 className="animate-spin" size={18} /> Loading stats…
              </div>
            ) : (
              <>
                <StatCard label="Total Recordings" value={stats.total_recordings} />
                <StatCard label="Native Contributors" value={stats.native_contributors} />
                <StatCard label="Average Quality" value={stats.average_quality} unit="%" />
                <StatCard label="Hours Collected" value={stats.hours_collected} unit="hrs" />
              </>
            )}
          </div>

          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {/* Leaderboard */}
            <Card>
              <h2 className="font-display flex items-center gap-2 text-lg font-bold text-ink">
                <Trophy size={18} className="text-marigold-deep" /> Top Contributors
              </h2>
              <ul className="mt-4 space-y-3">
                {!leaderboard ? (
                  <li className="text-sm text-ink-soft">Loading…</li>
                ) : (
                  leaderboard.map((entry, i) => (
                    <li
                      key={entry.username}
                      className="flex items-center justify-between rounded-xl bg-cream-deep/50 px-4 py-2.5"
                    >
                      <span className="flex items-center gap-3">
                        <span className="font-display flex h-7 w-7 items-center justify-center rounded-full bg-maroon text-xs font-bold text-cream">
                          {i + 1}
                        </span>
                        <span className="font-semibold text-ink">{entry.username}</span>
                        <Badge tone="neutral" className="text-[10px]">
                          {entry.region}
                        </Badge>
                      </span>
                      <span className="font-display font-bold text-maroon">
                        {entry.count}
                      </span>
                    </li>
                  ))
                )}
              </ul>
            </Card>

            {/* Achievements */}
            <Card>
              <h2 className="font-display text-lg font-bold text-ink">
                Achievements
              </h2>
              <ul className="mt-4 space-y-3">
                {MOCK_ACHIEVEMENTS.map((a) => (
                  <li
                    key={a.id}
                    className="flex items-center gap-3 rounded-xl bg-cream-deep/50 px-4 py-2.5"
                  >
                    <span className="text-xl">{a.emoji}</span>
                    <span className="font-medium text-ink">{a.label}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          {/* Regional accents */}
          <Card className="mt-6">
            <h2 className="font-display text-lg font-bold text-ink">
              Regional Accents
            </h2>
            <div className="mt-4 flex gap-3">
              {["Naga", "Albay"].map((region) => (
                <span
                  key={region}
                  className="flex items-center gap-1.5 rounded-full bg-marigold/15 px-4 py-2 text-sm font-semibold text-marigold-deep"
                >
                  <MapPin size={14} /> {region}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </>
  );
}
