import { CheckCircle2, XCircle, ArrowDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function ValidationResult({
  expected,
  transcript,
  score,
  accepted,
}: {
  expected: string;
  transcript: string;
  score: number;
  accepted: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border-2 p-6 text-center",
        accepted ? "border-leaf/30 bg-leaf/5" : "border-maroon/30 bg-maroon/5"
      )}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
        Expected
      </p>
      <p className="font-display mt-1 text-lg font-bold text-ink">
        &ldquo;{expected}&rdquo;
      </p>

      <ArrowDown className="mx-auto my-3 text-ink-soft" size={18} />

      <p className="text-xs font-semibold uppercase tracking-wide text-ink-soft">
        Whisper heard
      </p>
      <p className="font-display mt-1 text-lg font-bold text-ink">
        &ldquo;{transcript}&rdquo;
      </p>

      <div className="mt-5 flex items-center justify-center gap-2">
        <span
          className={cn(
            "font-display text-3xl font-extrabold",
            accepted ? "text-leaf" : "text-maroon"
          )}
        >
          {score}%
        </span>
        <span className="text-sm text-ink-soft">match</span>
      </div>

      <div
        className={cn(
          "mt-4 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-semibold",
          accepted ? "bg-leaf/15 text-leaf" : "bg-maroon/15 text-maroon"
        )}
      >
        {accepted ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
        {accepted ? "Accepted" : "Try again — below 90% match"}
      </div>
    </div>
  );
}
