import Link from "next/link";

import type { EntityRef } from "@/types/api";

export function EntityPill({ entity }: { entity: EntityRef }) {
  return (
    <Link
      href={`/entities/${entity.slug}`}
      className="rounded-full border border-ink/10 bg-white/80 px-3 py-1 text-sm text-slate transition hover:border-ink/20 hover:text-ink"
    >
      {entity.canonical_name}
    </Link>
  );
}
