import Link from "next/link";
import type { Route } from "next";

import { DashboardSummary } from "@/types/api";
import { AppFrame } from "@/components/app-frame";

type DashboardShellProps = {
  data: DashboardSummary;
};

function formatScore(value: number | null | undefined): string {
  return value === null || value === undefined ? "n/a" : value.toFixed(2);
}

export function DashboardShell({ data }: DashboardShellProps) {
  return (
    <AppFrame
      eyebrow="Dashboard"
      title="AI infrastructure signals arranged for strategy review, not feed consumption."
      description="The dashboard now sits on top of normalized and scored records, so each ranked card can expand into browseable entities, themes, and briefs."
      aside={
        <div className="rounded-[1.5rem] border border-ink/10 bg-ink p-6 text-mist">
          <p className="eyebrow !text-mist/70">Latest brief snapshot</p>
          {data.latest_brief ? (
            <div className="mt-4 space-y-3">
              <h2 className="text-2xl font-semibold">{data.latest_brief.title}</h2>
              <p className="text-sm uppercase tracking-[0.2em] text-mist/70">{data.latest_brief.brief_date}</p>
              <p className="text-sm leading-6 text-mist/90">{data.latest_brief.summary}</p>
              <p className="rounded-2xl bg-white/8 p-4 text-sm leading-6 text-mist/80">
                {data.latest_brief.aws_implications ?? "AWS implications will populate in later milestones."}
              </p>
              <Link href="/briefs/latest" className="inline-block text-sm text-mist underline-offset-4 hover:underline">
                Open latest brief
              </Link>
            </div>
          ) : (
            <p className="mt-4 text-sm text-mist/80">No brief found. Seed data should populate one.</p>
          )}
        </div>
      }
    >

      <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="eyebrow">Top events</p>
              <h2 className="mt-2 text-2xl font-semibold">Ranked signal board</h2>
            </div>
            <p className="text-sm text-slate">Score-first ordering from seeded event scores</p>
          </div>
          <div className="mt-6 space-y-4">
            {data.top_events.map((event, index) => (
              <div key={event.id} className="rounded-[1.4rem] border border-ink/10 bg-white/70 p-5">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <p className="eyebrow">
                      #{index + 1} · {event.event_type.replaceAll("_", " ")}
                    </p>
                    <h3 className="text-xl font-semibold">
                      <Link href={`/events/${event.id}` as Route}>{event.title}</Link>
                    </h3>
                    <p className="text-sm leading-6 text-slate">{event.summary}</p>
                    <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-slate">
                      <span>{new Date(event.occurred_at).toLocaleDateString()}</span>
                      {event.source_type ? <span>{event.source_type}</span> : null}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-ink/10 bg-mist px-4 py-3 text-right">
                    <p className="eyebrow">Radar score</p>
                    <p className="mt-1 text-2xl font-semibold text-ember">{formatScore(event.radar_score)}</p>
                    {event.source_type ? <p className="mt-2 text-xs text-slate">{event.source_type}</p> : null}
                    {event.source_url ? (
                      <a href={event.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs text-ember underline-offset-4 hover:underline">
                        Open source
                      </a>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
            {data.top_events.length === 0 ? <p className="text-sm text-slate">No seeded events available yet.</p> : null}
          </div>
        </article>

        <div className="grid gap-6">
          <article className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">Emerging entities</p>
            <h2 className="mt-2 text-2xl font-semibold">Priority movers</h2>
            <div className="mt-5 space-y-4">
              {data.emerging_entities.map((entity) => (
                <div key={entity.id} className="rounded-[1.3rem] border border-ink/10 bg-white/70 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold">
                        <Link href={`/entities/${entity.slug}` as Route}>{entity.canonical_name}</Link>
                      </h3>
                      <p className="text-sm text-slate">{entity.entity_type}</p>
                    </div>
                    <p className="text-xl font-semibold text-moss">{formatScore(entity.entity_priority_score)}</p>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate">
                    <div>Momentum: {formatScore(entity.momentum_score)}</div>
                    <div>CorpDev: {formatScore(entity.corpdev_interest_score)}</div>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">Theme heat map</p>
            <h2 className="mt-2 text-2xl font-semibold">Entity density by theme</h2>
            <div className="mt-5 space-y-3">
              {data.theme_heatmap.map((theme) => (
                <div key={theme.id}>
                  <div className="mb-2 flex items-center justify-between text-sm text-slate">
                    <span>{theme.name}</span>
                    <span>{theme.entity_count} linked</span>
                  </div>
                  <div className="h-3 rounded-full bg-ink/8">
                    <Link href={`/themes/${theme.slug}` as Route} className="block">
                      <div
                        className="h-3 rounded-full bg-gradient-to-r from-ember to-moss"
                        style={{ width: `${Math.min(theme.entity_count * 26, 100)}%` }}
                      />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Opportunity queue</p>
          <h2 className="mt-2 text-2xl font-semibold">Rule-based CorpDev hypotheses</h2>
          <div className="mt-5 space-y-4">
            {data.opportunities.map((opportunity) => (
              <div key={opportunity.id} className="rounded-[1.3rem] border border-ink/10 bg-white/70 p-4">
                <div className="flex items-center justify-between gap-4">
                  <h3 className="text-lg font-semibold">{opportunity.title}</h3>
                  <span className="rounded-full bg-ink px-3 py-1 text-xs uppercase tracking-[0.2em] text-mist">
                    {opportunity.opportunity_type}
                  </span>
                </div>
                <p className="mt-3 text-sm text-slate">Priority: {formatScore(opportunity.priority_score)}</p>
              </div>
            ))}
            {data.opportunities.length === 0 ? (
              <p className="text-sm text-slate">No seeded opportunities available yet.</p>
            ) : null}
          </div>
        </article>

        <article className="panel rounded-[1.75rem] p-6 md:p-8">
          <p className="eyebrow">Local stack status</p>
          <h2 className="mt-2 text-2xl font-semibold">Current build checkpoints</h2>
          <ul className="mt-5 space-y-3 text-sm leading-6 text-slate">
            <li>Adapters persist source documents and raw payloads with idempotent fingerprints.</li>
            <li>Normalization produces canonical entities, theme links, and one primary event per source document.</li>
            <li>Scoring is deterministic and versioned through `rationale_json` on event and entity score rows.</li>
            <li>The browse pages now sit on top of the API surface rather than seed-only assumptions.</li>
          </ul>
        </article>
      </section>
    </AppFrame>
  );
}
