import Link from "next/link";
import type { Route } from "next";

import { AppFrame } from "@/components/app-frame";
import { fetchSearch } from "@/lib/api";

type SearchPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function getQuery(searchParams: Record<string, string | string[] | undefined> | undefined): string {
  const value = searchParams?.q;
  return typeof value === "string" ? value : "";
}

function isInternalHref(href: string | null): href is `/${string}` {
  return Boolean(href?.startsWith("/"));
}

function ResultSection({
  title,
  items
}: {
  title: string;
  items: { id: string; title: string; subtitle: string | null; snippet: string | null; href: string | null; score: number | null }[];
}) {
  return (
    <article className="panel rounded-[1.75rem] p-6 md:p-8">
      <p className="eyebrow">{title}</p>
      <div className="mt-5 space-y-4">
        {items.map((item) => (
          <div key={item.id} className="rounded-[1.3rem] border border-ink/10 bg-white/70 p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="space-y-2">
                <h2 className="text-xl font-semibold">
                  {isInternalHref(item.href) ? <Link href={item.href as Route}>{item.title}</Link> : item.title}
                </h2>
                <p className="text-sm text-slate">{item.subtitle}</p>
                <p className="text-sm leading-6 text-slate">{item.snippet}</p>
                {item.href && !isInternalHref(item.href) ? (
                  <a href={item.href} target="_blank" rel="noreferrer" className="text-sm text-ember underline-offset-4 hover:underline">
                    Open source
                  </a>
                ) : null}
              </div>
              <div className="rounded-2xl border border-ink/10 bg-white px-4 py-3 text-right text-sm text-slate">
                Score: {item.score?.toFixed(2) ?? "n/a"}
              </div>
            </div>
          </div>
        ))}
        {items.length === 0 ? <p className="text-sm text-slate">No matches.</p> : null}
      </div>
    </article>
  );
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolvedSearchParams = await searchParams;
  const query = getQuery(resolvedSearchParams);
  const results = await fetchSearch(query, 10);

  return (
    <AppFrame
      eyebrow="Search"
      title="Keyword search across events, entities, and source documents."
      description="This is the deterministic keyword path for now. Semantic retrieval can slot in later on the same page shape."
      aside={
        <form action="/search" className="grid gap-3">
          <input name="q" defaultValue={query} placeholder="Search entities, events, or source text" className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none" />
          <button className="rounded-2xl bg-ink px-4 py-3 text-sm font-medium text-mist">Search</button>
        </form>
      }
    >
      <section className="grid gap-6">
        <ResultSection title="Events" items={results.events} />
        <ResultSection title="Entities" items={results.entities} />
        <ResultSection title="Documents" items={results.documents} />
      </section>
    </AppFrame>
  );
}
