import Link from "next/link";
import type { Route } from "next";
import { notFound } from "next/navigation";

import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { ScoreChip } from "@/components/score-chip";
import { fetchTheme } from "@/lib/api";

export default async function ThemeDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const theme = await fetchTheme(slug);
  if (!theme) {
    notFound();
  }

  return (
    <AppFrame
      eyebrow="Theme"
      title={theme.name}
      description={theme.description ?? "No description available for this theme."}
      aside={
        <div className="grid gap-3">
          <ScoreChip label="Linked entities" value={theme.entity_count} />
          <p className="text-sm leading-6 text-slate">
            Theme detail is derived from entity links and scored events, which keeps the page explainable and deterministic.
          </p>
        </div>
      }
    >
      <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Linked entities</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {theme.linked_entities.map((entity) => (
              <EntityPill key={entity.id} entity={entity} />
            ))}
          </div>
        </article>

        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Top events</p>
          <div className="mt-5 space-y-4">
            {theme.top_events.map((event) => (
              <div key={event.id} className="rounded-[1.3rem] border border-ink/10 bg-white/70 p-5">
                <div className="flex flex-col gap-3 md:flex-row md:justify-between">
                  <div className="space-y-2">
                    <p className="eyebrow">{event.event_type.replaceAll("_", " ")}</p>
                    <h2 className="text-xl font-semibold">
                      <Link href={`/events/${event.id}` as Route}>{event.title}</Link>
                    </h2>
                    <p className="text-sm leading-6 text-slate">{event.summary}</p>
                  </div>
                  <ScoreChip label="Radar" value={event.radar_score} />
                </div>
              </div>
            ))}
            {theme.top_events.length === 0 ? <p className="text-sm text-slate">No scored events linked to this theme yet.</p> : null}
          </div>
        </article>
      </section>
    </AppFrame>
  );
}
