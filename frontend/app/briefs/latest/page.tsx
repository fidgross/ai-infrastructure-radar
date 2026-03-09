import Link from "next/link";
import type { Route } from "next";

import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { fetchLatestBrief } from "@/lib/api";

export default async function LatestBriefPage() {
  const brief = await fetchLatestBrief();

  return (
    <AppFrame
      eyebrow="Daily brief"
      title={brief?.title ?? "No brief available"}
      description={brief?.summary ?? "Generate or seed a brief to populate this page."}
      aside={
        <div className="space-y-4 text-sm leading-6 text-slate">
          {brief?.brief_date ? <p>Brief date: {brief.brief_date}</p> : null}
          <p>{brief?.aws_implications ?? "AWS implications will appear here once a brief exists."}</p>
          {brief?.possible_actions ? <p>Possible actions: {brief.possible_actions}</p> : null}
          {brief?.skeptical_counterpoints ? <p>Skeptical counterpoints: {brief.skeptical_counterpoints}</p> : null}
        </div>
      }
    >
      <section className="grid gap-4">
        {brief?.items.map((item) => (
          <article key={item.id} className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">
              {item.item_type.replaceAll("_", " ")} · rank {item.rank}
            </p>
            <h2 className="mt-2 text-2xl font-semibold">{item.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate">{item.summary}</p>
            {item.event ? (
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate">
                <span>Radar: {item.event.radar_score?.toFixed(2) ?? "n/a"}</span>
                <Link href={`/events/${item.event.id}` as Route} className="text-ember underline-offset-4 hover:underline">
                  Open event
                </Link>
              </div>
            ) : null}
            {item.entity ? (
              <div className="mt-4 flex flex-wrap gap-2">
                <EntityPill entity={item.entity} />
              </div>
            ) : null}
          </article>
        )) ?? <p className="text-sm text-slate">No brief items found.</p>}
      </section>
    </AppFrame>
  );
}
