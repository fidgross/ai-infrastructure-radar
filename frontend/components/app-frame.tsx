import type { ReactNode } from "react";
import Link from "next/link";
import type { Route } from "next";

type AppFrameProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  aside?: ReactNode;
};

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/events", label: "Events" },
  { href: "/entities", label: "Entities" },
  { href: "/themes", label: "Themes" },
  { href: "/search", label: "Search" },
  { href: "/briefs/latest", label: "Brief" },
  { href: "/opportunities", label: "Opportunities" },
  { href: "/watchlists", label: "Watchlists" }
] as const satisfies ReadonlyArray<{ href: Route; label: string }>;

export function AppFrame({ eyebrow, title, description, children, aside }: AppFrameProps) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-5 py-8 md:px-8 md:py-12">
      <nav className="panel flex flex-wrap items-center justify-between gap-4 rounded-[1.75rem] px-5 py-4 md:px-7">
        <div>
          <p className="eyebrow">AI Infrastructure Radar</p>
          <p className="text-sm text-slate">Local strategy intelligence workbench</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full border border-ink/10 bg-white/70 px-4 py-2 text-sm text-slate transition hover:border-ink/20 hover:text-ink"
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="panel rounded-[1.9rem] px-6 py-8 md:px-8">
          <p className="eyebrow">{eyebrow}</p>
          <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-tight md:text-5xl">{title}</h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-slate">{description}</p>
        </div>
        <aside className="panel rounded-[1.9rem] px-6 py-8 md:px-8">{aside}</aside>
      </section>

      {children}
    </main>
  );
}
