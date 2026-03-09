import { notFound } from "next/navigation";

import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { ScoreChip } from "@/components/score-chip";
import { ThemePill } from "@/components/theme-pill";
import { fetchEvent } from "@/lib/api";

export default async function EventDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const event = await fetchEvent(id);
  if (!event) {
    notFound();
  }

  return (
    <AppFrame
      eyebrow={event.event_type.replaceAll("_", " ")}
      title={event.title}
      description={event.summary ?? "No event summary is available yet."}
      aside={
        <div className="grid grid-cols-2 gap-3">
          <ScoreChip label="Radar" value={event.score?.radar_score ?? event.radar_score} />
          <ScoreChip label="Confidence" value={event.confidence} />
          <ScoreChip label="Novelty" value={event.score?.novelty_score} />
          <ScoreChip label="Momentum" value={event.score?.momentum_score} />
          <ScoreChip label="AWS" value={event.score?.aws_relevance_score} />
          <ScoreChip label="CorpDev" value={event.score?.corpdev_score} />
        </div>
      }
    >
      <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Context</p>
          <div className="mt-5 space-y-4 text-sm leading-6 text-slate">
            <p>
              <strong className="text-ink">Occurred:</strong> {new Date(event.occurred_at).toLocaleString()}
            </p>
            <p>
              <strong className="text-ink">Detected:</strong> {new Date(event.detected_at).toLocaleString()}
            </p>
            {event.stack_layer ? (
              <p>
                <strong className="text-ink">Stack layer:</strong> {event.stack_layer}
              </p>
            ) : null}
            {event.source ? (
              <a href={event.source.url} target="_blank" rel="noreferrer" className="inline-block text-sm text-ember underline-offset-4 hover:underline">
                Open source document
              </a>
            ) : null}
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <p className="eyebrow">Why it matters</p>
              <p className="mt-2 text-sm leading-6 text-slate">{event.why_it_matters ?? "Not yet captured."}</p>
            </div>
            <div>
              <p className="eyebrow">Skeptical note</p>
              <p className="mt-2 text-sm leading-6 text-slate">{event.skeptical_note ?? "No skeptical note recorded yet."}</p>
            </div>
          </div>
        </article>

        <div className="grid gap-6">
          <article className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">Linked entities</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {event.linked_entities.map((entity) => (
                <EntityPill key={entity.id} entity={entity} />
              ))}
            </div>
            {event.linked_entities.length === 0 ? <p className="mt-4 text-sm text-slate">No entities linked yet.</p> : null}
          </article>

          <article className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">Themes</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {event.themes.map((theme) => (
                <ThemePill key={theme.slug} theme={theme} />
              ))}
            </div>
            {event.themes.length === 0 ? <p className="mt-4 text-sm text-slate">No themes linked yet.</p> : null}
          </article>

          <article className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">Score rationale</p>
            <pre className="mt-4 overflow-x-auto rounded-[1.3rem] border border-ink/10 bg-white/70 p-4 text-xs leading-6 text-slate">
              {JSON.stringify(event.score?.rationale_json ?? event.metadata_json, null, 2)}
            </pre>
          </article>
        </div>
      </section>
    </AppFrame>
  );
}
