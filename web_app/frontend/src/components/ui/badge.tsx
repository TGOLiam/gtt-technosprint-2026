import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

type BadgeTone = "leaf" | "marigold" | "maroon" | "neutral";

const toneClasses: Record<BadgeTone, string> = {
  leaf: "bg-leaf/10 text-leaf border-leaf/30",
  marigold: "bg-marigold/15 text-marigold-deep border-marigold/40",
  maroon: "bg-maroon/10 text-maroon border-maroon/30",
  neutral: "bg-ink/5 text-ink-soft border-ink/15",
};

export function Badge({
  className,
  tone = "neutral",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}
