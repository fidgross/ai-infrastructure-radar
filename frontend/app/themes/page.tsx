import Link from "next/link";
import type { Route } from "next";

import { AppFrame } from "@/components/app-frame";
import { fetchThemes } from "@/lib/api";

type ThemesPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function getParam(searchParams: Record<string, string | string[] | undefined> | undefined, key: string): string {
  const value = searchParams?.[key];
  return typeof value === "string" ? value : "";
}

export default async function ThemesPage({ searchParams }: ThemesPageProps) {
  const resolvedSearchParams = await searchParams;
  const sort = getParam(resolvedSearchParams, "sort") || undefined;
  const response = await fetchThemes({ sort });

  return (
    <AppFrame
      eyebrow="Themes"
      title="Theme browse view over the normalized graph."
      description="Each theme is backed by entity-theme links and can pivot into the top scored events attached to that slice of the market."
      aside={
        <form action="/themes" className="grid gap-3">
          <input name="sort" defaultValue={getParam(resolvedSearchParams, "sort")} placeholder="entity_count or name" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <button className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-mist">Apply sort</button>
        </form>
      }
    >
      <section className="grid gap-5 md:grid-cols-2">
        {response.items.map((theme) => (
          <article key={theme.id} className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">{theme.entity_count} linked entities</p>
            <h2 className="mt-2 text-2xl font-semibold">
              <Link href={`/themes/${theme.slug}` as Route}>{theme.name}</Link>
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate">{theme.description ?? "No theme description available yet."}</p>
          </article>
        ))}
        {response.items.length === 0 ? <p className="text-sm text-slate">No themes are available yet.</p> : null}
      </section>
    </AppFrame>
  );
}
