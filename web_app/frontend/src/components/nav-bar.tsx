"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Mic } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/record", label: "Record" },
  { href: "/about", label: "About" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b-2 border-ink/10 bg-cream/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-maroon text-cream">
            <Mic size={18} strokeWidth={2.5} />
          </span>
          <span className="font-display text-xl font-bold tracking-tight text-ink">
            TinigBicol
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
                pathname === link.href
                  ? "bg-maroon text-cream"
                  : "text-ink-soft hover:bg-ink/5 hover:text-ink"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <Link
          href="/record"
          className="md:hidden rounded-full bg-maroon text-cream px-4 py-2 text-sm font-semibold"
        >
          Record
        </Link>
      </div>
    </header>
  );
}
