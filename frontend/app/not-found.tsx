import Link from "next/link";

import { AppFrame } from "@/components/app-frame";

export default function NotFoundPage() {
  return (
    <AppFrame
      eyebrow="Not found"
      title="The requested record was not found."
      description="This usually means the local database has not been seeded or the slug does not exist yet."
      aside={<Link href="/" className="text-sm text-ember underline-offset-4 hover:underline">Back to dashboard</Link>}
    >
      <section className="panel rounded-[1.75rem] p-6 md:p-8">
        <p className="text-sm leading-6 text-slate">Run the local bootstrap and seed flow, then try the page again.</p>
      </section>
    </AppFrame>
  );
}
