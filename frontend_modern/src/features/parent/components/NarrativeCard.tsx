import { Badge } from '@/shared/ui';
import type { ParentProgressSummary } from '../useParentSummary';

interface Props {
  summary: ParentProgressSummary;
}

const formatDate = (iso: string): string => {
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return iso;
  }
};

const StatTile = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg bg-ink-50 px-3 py-2">
    <p className="text-xs text-ink-500 font-medium">{label}</p>
    <p className="text-base font-semibold text-ink-900 mt-0.5">{value}</p>
  </div>
);

export const NarrativeCard = ({ summary }: Props) => {
  const weekRange = `${formatDate(summary.week_start)} – ${formatDate(summary.week_end)}`;
  const deltaPct = Math.round(summary.score_delta * 100);
  const deltaSign = summary.score_delta > 0 ? '+' : '';
  const deltaColor =
    summary.score_delta > 0.01
      ? 'text-emerald-700 bg-emerald-50'
      : summary.score_delta < -0.01
        ? 'text-rose-700 bg-rose-50'
        : 'text-ink-700 bg-ink-100';

  return (
    <article className="os-card p-5 sm:p-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-500 font-medium">
            Weekly summary · {summary.child_name}
          </p>
          <p className="text-sm text-ink-500 mt-1">{weekRange}</p>
        </div>
        <Badge tone="brand">{summary.model_used}</Badge>
      </div>

      <p className="mt-4 text-ink-800 leading-relaxed whitespace-pre-line">
        {summary.summary_text}
      </p>

      <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-2">
        <StatTile label="Questions" value={String(summary.ticks_recorded)} />
        <StatTile label="Active days" value={`${summary.active_days} / 7`} />
        <StatTile label="Avg score" value={`${Math.round(summary.avg_score * 100)}%`} />
        <div className={`rounded-lg px-3 py-2 ${deltaColor}`}>
          <p className="text-xs font-medium opacity-80">Vs last week</p>
          <p className="text-base font-semibold mt-0.5">
            {deltaSign}
            {deltaPct}%
          </p>
        </div>
      </div>
    </article>
  );
};
