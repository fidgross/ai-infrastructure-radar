import Link from "next/link";
import type { Route } from "next";

import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { ScoreChip } from "@/components/score-chip";
import { ThemePill } from "@/components/theme-pill";
import { fetchEvents } from "@/lib/api";

type EventsPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function getParam(searchParams: Record<string, string | string[] | undefined> | undefined, key: string): string {
  const value = searchParams?.[key];
  return typeof value === "string" ? value : "";
}

export default async function EventsPage({ searchParams }: EventsPageProps) {
  const resolvedSearchParams = await searchParams;
  const filters = {
    source_type: getParam(resolvedSearchParams, "source_type") || undefined,
    event_type: getParam(resolvedSearchParams, "event_type") || undefined,
    theme_slug: getParam(resolvedSearchParams, "theme_slug") || undefined,
    min_score: getParam(resolvedSearchParams, "min_score") || undefined
  };
  const response = await fetchEvents(filters);

  return (
    <AppFrame
      eyebrow="Events"
      title="Ranked events with source attribution and deterministic scores."
      description="Use lightweight GET filters now; richer interactive controls can sit on the same backend contracts later."
      aside={
        <form action="/events" className="grid gap-3">
          <input name="source_type" defaultValue={getParam(resolvedSearchParams, "source_type")} placeholder="source type" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <input name="event_type" defaultValue={getParam(resolvedSearchParams, "event_type")} placeholder="event type" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <input name="theme_slug" defaultValue={getParam(resolvedSearchParams, "theme_slug")} placeholder="theme slug" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <input name="min_score" defaultValue={getParam(resolvedSearchParams, "min_score")} placeholder="min radar score" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <button className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-mist">Apply filters</button>
        </form>
      }
    >
      <section className="grid gap-5">
        {response.items.map((event) => (
          <article key={event.id} className="panel rounded-[1.75rem] p-6 md:p-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                <p className="eyebrow">{event.event_type.replaceAll("_", " ")}</p>
                <h2 className="text-2xl font-semibold">
                  <Link href={`/events/${event.id}` as Route}>{event.title}</Link>
                </h2>
                <p className="max-w-3xl text-sm leading-6 text-slate">{event.summary}</p>
                <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-slate">
                  <span>{new Date(event.occurred_at).toLocaleDateString()}</span>
                  {event.source?.source_type ? <span>{event.source.source_type}</span> : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  {event.linked_entities.map((entity) => (
                    <EntityPill key={entity.id} entity={entity} />
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {event.themes.map((theme) => (
                    <ThemePill key={`${event.id}-${theme.slug}`} theme={theme} />
                  ))}
                </div>
                {event.source ? (
                  <a href={event.source.url} target="_blank" rel="noreferrer" className="inline-block text-sm text-ember underline-offset-4 hover:underline">
                    Open source document
                  </a>
                ) : null}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <ScoreChip label="Radar" value={event.radar_score} />
                <ScoreChip label="Confidence" value={event.confidence} />
              </div>
            </div>
          </article>
        ))}
        {response.items.length === 0 ? <p className="text-sm text-slate">No events matched the current filter set.</p> : null}
      </section>
    </AppFrame>
  );
}
