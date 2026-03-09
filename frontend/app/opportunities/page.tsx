import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { ScoreChip } from "@/components/score-chip";
import { ThemePill } from "@/components/theme-pill";
import { fetchOpportunities } from "@/lib/api";

export default async function OpportunitiesPage() {
  const response = await fetchOpportunities();

  return (
    <AppFrame
      eyebrow="Opportunities"
      title="Transparent rule-driven opportunity queue."
      description="These are derived from scored entities and events, not freeform synthesis, so they stay inspectable."
      aside={<p className="text-sm leading-6 text-slate">Milestone 5 can enrich this with watchlist triggers and analyst notes without changing the page shape.</p>}
    >
      <section className="grid gap-5">
        {response.items.map((opportunity) => (
          <article key={opportunity.id} className="panel rounded-[1.75rem] p-6 md:p-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                <p className="eyebrow">{opportunity.opportunity_type}</p>
                <h2 className="text-2xl font-semibold">{opportunity.title}</h2>
                <p className="text-sm leading-6 text-slate">{opportunity.rationale}</p>
                {opportunity.risks ? <p className="text-sm leading-6 text-slate">Risks: {opportunity.risks}</p> : null}
                <div className="flex flex-wrap gap-2">
                  {opportunity.entity ? <EntityPill entity={opportunity.entity} /> : null}
                  {opportunity.theme ? <ThemePill theme={opportunity.theme} /> : null}
                </div>
              </div>
              <div className="grid gap-3">
                <ScoreChip label="Priority" value={opportunity.priority_score} />
                <div className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm text-slate">{opportunity.status}</div>
              </div>
            </div>
          </article>
        ))}
        {response.items.length === 0 ? <p className="text-sm text-slate">No opportunities are available yet.</p> : null}
      </section>
    </AppFrame>
  );
}
