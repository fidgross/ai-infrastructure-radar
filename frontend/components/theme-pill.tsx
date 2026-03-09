import Link from "next/link";

import type { ThemeRef } from "@/types/api";

export function ThemePill({ theme }: { theme: ThemeRef }) {
  return (
    <Link
      href={`/themes/${theme.slug}`}
      className="rounded-full border border-ink/10 bg-mist px-3 py-1 text-sm text-slate transition hover:border-ink/20 hover:text-ink"
    >
      {theme.name}
    </Link>
  );
}
