type ScoreChipProps = {
  label: string;
  value: number | null | undefined;
};

function formatScore(value: number | null | undefined): string {
  return value === null || value === undefined ? "n/a" : value.toFixed(2);
}

export function ScoreChip({ label, value }: ScoreChipProps) {
  return (
    <div className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3">
      <p className="eyebrow">{label}</p>
      <p className="mt-1 text-xl font-semibold text-ember">{formatScore(value)}</p>
    </div>
  );
}
