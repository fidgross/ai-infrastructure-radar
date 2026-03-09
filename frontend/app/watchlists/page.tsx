import { AppFrame } from "@/components/app-frame";
import { EntityPill } from "@/components/entity-pill";
import { ThemePill } from "@/components/theme-pill";
import { fetchWatchlists } from "@/lib/api";

export default async function WatchlistsPage() {
  const response = await fetchWatchlists();

  return (
    <AppFrame
      eyebrow="Watchlists"
      title="Current watchlists and tracked entities."
      description="The API already supports creating watchlists and adding items; this page is the browse-first shell for local mode."
      aside={
        <div className="space-y-3 text-sm leading-6 text-slate">
          <p>{"Use `POST /api/watchlists` and `POST /api/watchlists/{watchlist_id}/items` to mutate data while the UI remains browse-first."}</p>
          <p>This keeps Milestone 4 focused on stable read contracts.</p>
        </div>
      }
    >
      <section className="grid gap-5">
        {response.items.map((watchlist) => (
          <article key={watchlist.id} className="panel rounded-[1.75rem] p-6 md:p-8">
            <p className="eyebrow">{watchlist.watchlist_type}</p>
            <h2 className="mt-2 text-2xl font-semibold">{watchlist.name}</h2>
            <p className="mt-3 text-sm leading-6 text-slate">{watchlist.description}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {watchlist.items.map((item) =>
                item.entity ? <EntityPill key={item.id} entity={item.entity} /> : item.theme ? <ThemePill key={item.id} theme={item.theme} /> : null
              )}
            </div>
          </article>
        ))}
        {response.items.length === 0 ? <p className="text-sm text-slate">No watchlists are available yet.</p> : null}
      </section>
    </AppFrame>
  );
}
