import Link from "next/link";
import type { Route } from "next";
import { notFound } from "next/navigation";

import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { ScoreChip } from "@/components/score-chip";
import { ThemePill } from "@/components/theme-pill";
import { fetchEntity } from "@/lib/api";

export default async function EntityDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const entity = await fetchEntity(slug);
  if (!entity) {
    notFound();
  }

  return (
    <AppFrame
      eyebrow={entity.entity_type}
      title={entity.canonical_name}
      description={entity.description ?? "No analyst summary is available for this entity yet."}
      aside={
        <div className="grid grid-cols-2 gap-3">
          <ScoreChip label="Priority" value={entity.score?.entity_priority_score} />
          <ScoreChip label="Momentum" value={entity.score?.momentum_score} />
          <ScoreChip label="AWS" value={entity.score?.aws_relevance_score} />
          <ScoreChip label="CorpDev" value={entity.score?.corpdev_interest_score} />
        </div>
      }
    >
      <section className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Themes and aliases</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {entity.themes.map((theme) => (
              <ThemePill key={theme.slug} theme={theme} />
            ))}
          </div>
          <div className="mt-6 space-y-2 text-sm text-slate">
            {entity.aliases.map((alias) => (
              <div key={alias} className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3">
                {alias}
              </div>
            ))}
          </div>
          {entity.website ? (
            <a href={entity.website} target="_blank" rel="noreferrer" className="mt-6 inline-block text-sm text-ember underline-offset-4 hover:underline">
              Visit primary link
            </a>
          ) : null}
        </article>

        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Event timeline</p>
          <div className="mt-5 space-y-4">
            {entity.linked_events.map((event) => (
              <div key={event.id} className="rounded-[1.3rem] border border-ink/10 bg-white/70 p-5">
                <div className="flex flex-col gap-3 md:flex-row md:justify-between">
                  <div className="space-y-2">
                    <p className="eyebrow">{event.event_type.replaceAll("_", " ")}</p>
                    <h2 className="text-xl font-semibold">
                      <Link href={`/events/${event.id}` as Route}>{event.title}</Link>
                    </h2>
                    <p className="text-sm leading-6 text-slate">{event.summary}</p>
                    <div className="flex flex-wrap gap-2">
                      {event.linked_entities.map((linked) => (
                        <EntityPill key={linked.id} entity={linked} />
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {event.themes.map((theme) => (
                        <ThemePill key={`${event.id}-${theme.slug}`} theme={theme} />
                      ))}
                    </div>
                  </div>
                  <ScoreChip label="Radar" value={event.radar_score} />
                </div>
              </div>
            ))}
            {entity.linked_events.length === 0 ? <p className="text-sm text-slate">No linked events yet.</p> : null}
          </div>
        </article>
      </section>
    </AppFrame>
  );
}
