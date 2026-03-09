import Link from "next/link";
import type { Route } from "next";

import { AppFrame } from "@/components/app-frame";
import { ScoreChip } from "@/components/score-chip";
import { ThemePill } from "@/components/theme-pill";
import { fetchEntities } from "@/lib/api";

type EntitiesPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function getParam(searchParams: Record<string, string | string[] | undefined> | undefined, key: string): string {
  const value = searchParams?.[key];
  return typeof value === "string" ? value : "";
}

export default async function EntitiesPage({ searchParams }: EntitiesPageProps) {
  const resolvedSearchParams = await searchParams;
  const filters = {
    entity_type: getParam(resolvedSearchParams, "entity_type") || undefined,
    theme_slug: getParam(resolvedSearchParams, "theme_slug") || undefined,
    min_priority: getParam(resolvedSearchParams, "min_priority") || undefined
  };
  const response = await fetchEntities(filters);

  return (
    <AppFrame
      eyebrow="Entities"
      title="Canonical entities with linked themes and priority scores."
      description="This is the browse-first view over normalized entities, so aliases, themes, and linked events all resolve from a single canonical record."
      aside={
        <form action="/entities" className="grid gap-3">
          <input name="entity_type" defaultValue={getParam(resolvedSearchParams, "entity_type")} placeholder="entity type" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <input name="theme_slug" defaultValue={getParam(resolvedSearchParams, "theme_slug")} placeholder="theme slug" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <input name="min_priority" defaultValue={getParam(resolvedSearchParams, "min_priority")} placeholder="min priority" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <button className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-mist">Apply filters</button>
        </form>
      }
    >
      <section className="grid gap-5">
        {response.items.map((entity) => (
          <article key={entity.id} className="panel rounded-[1.75rem] p-6 md:p-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                <p className="eyebrow">{entity.entity_type}</p>
                <h2 className="text-2xl font-semibold">
                  <Link href={`/entities/${entity.slug}` as Route}>{entity.canonical_name}</Link>
                </h2>
                <p className="max-w-3xl text-sm leading-6 text-slate">{entity.description ?? "No description available yet."}</p>
                <div className="flex flex-wrap gap-2">
                  {entity.themes.map((theme) => (
                    <ThemePill key={`${entity.id}-${theme.slug}`} theme={theme} />
                  ))}
                </div>
                {entity.aliases.length > 0 ? (
                  <p className="text-sm text-slate">Aliases: {entity.aliases.join(", ")}</p>
                ) : null}
              </div>
              <div className="grid gap-3">
                <ScoreChip label="Priority" value={entity.score?.entity_priority_score} />
                <ScoreChip label="Momentum" value={entity.score?.momentum_score} />
              </div>
            </div>
          </article>
        ))}
        {response.items.length === 0 ? <p className="text-sm text-slate">No entities matched the current filter set.</p> : null}
      </section>
    </AppFrame>
  );
}
