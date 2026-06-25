import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

export function Card({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border-2 border-ink/10 bg-white/70 backdrop-blur-sm p-6",
        className
      )}
      {...props}
    />
  );
}

export function StatCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: string | number;
  unit?: string;
}) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-sm font-medium text-ink-soft uppercase tracking-wide">
        {label}
      </span>
      <span className="font-display text-4xl font-bold text-maroon">
        {value}
        {unit && <span className="text-xl ml-1 font-sans font-medium text-ink-soft">{unit}</span>}
      </span>
    </Card>
  );
}
