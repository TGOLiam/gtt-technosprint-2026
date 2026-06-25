"use client";

import { useEffect, useState } from "react";

export function LoadingScreen({ onDone }: { onDone: () => void }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const exitTimer = setTimeout(() => setExiting(true), 1600);
    const doneTimer = setTimeout(onDone, 2000);
    return () => {
      clearTimeout(exitTimer);
      clearTimeout(doneTimer);
    };
  }, [onDone]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-maroon transition-opacity duration-400 ${
        exiting ? "opacity-0" : "opacity-100"
      }`}
    >
      <div className="flex items-end gap-1.5 h-12">
        {[0, 1, 2, 3, 4].map((i) => (
          <span
            key={i}
            className="wave-bar w-2.5 rounded-full bg-marigold"
            style={{
              height: "100%",
              animationDelay: `${i * 0.12}s`,
            }}
          />
        ))}
      </div>
      <p className="mt-6 font-display text-lg font-semibold text-cream tracking-wide">
        TinigBicol
      </p>
    </div>
  );
}
