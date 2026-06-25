import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "outline";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-maroon text-cream hover:bg-maroon-light shadow-[3px_3px_0_0_rgba(36,27,20,0.18)] hover:shadow-[1px_1px_0_0_rgba(36,27,20,0.18)] hover:translate-x-[2px] hover:translate-y-[2px]",
  secondary:
    "bg-marigold text-ink hover:bg-marigold-deep shadow-[3px_3px_0_0_rgba(36,27,20,0.18)] hover:shadow-[1px_1px_0_0_rgba(36,27,20,0.18)] hover:translate-x-[2px] hover:translate-y-[2px]",
  outline:
    "bg-transparent border-2 border-ink text-ink hover:bg-ink hover:text-cream",
  ghost: "bg-transparent text-ink hover:bg-ink/5",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-base",
  lg: "px-8 py-4 text-lg",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-150 disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-maroon",
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
