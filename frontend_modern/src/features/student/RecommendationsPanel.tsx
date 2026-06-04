import { useRecommendations } from './useRecommendations';
import { usePracticePlan } from './usePracticePlan';

const PRIORITY_BADGE: Record<number, string> = {
  1: 'bg-rose-100 text-rose-800 border border-rose-300',
  2: 'bg-amber-100 text-amber-800 border border-amber-300',
  3: 'bg-brand-100 text-brand-800 border border-brand-300',
  4: 'bg-ink-100 text-ink-700 border border-ink-200',
};

export const RecommendationsPanel = () => {
  const { data: recommendations, isLoading } = useRecommendations();
  const { data: plan } = usePracticePlan();

  if (isLoading) return null;
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="os-card border-brand-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-display font-semibold text-ink-900">What to Practice Next</h2>
        {plan && (
          <span className="text-xs text-ink-500">
            Today&apos;s plan: ~{plan.estimated_minutes} min
          </span>
        )}
      </div>

      <div className="space-y-3">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="flex items-start justify-between gap-3 py-2 border-b border-ink-100 last:border-0"
          >
            <div className="flex items-start gap-3 min-w-0">
              <span
                className={`mt-0.5 shrink-0 text-xs font-semibold px-2 py-0.5 rounded ${PRIORITY_BADGE[rec.priority] ?? PRIORITY_BADGE[3]}`}
              >
                {rec.priority_display.toUpperCase()}
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink-900 truncate">{rec.chapter_name}</p>
                <p className="text-xs text-ink-500 mt-0.5">{rec.reason_display}</p>
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="text-sm font-semibold text-ink-700">
                {Math.round(rec.score_snapshot * 100)}%
              </p>
            </div>
          </div>
        ))}
      </div>

      {plan && (
        <div className="mt-4 pt-3 border-t border-ink-100 flex items-center justify-between">
          <span className="text-xs text-ink-500">
            {plan.recommendations.length} topic{plan.recommendations.length !== 1 ? 's' : ''} in today&apos;s plan
          </span>
          <div className="flex items-center gap-3">
            <a
              href="/student/proficiency"
              className="text-xs font-medium text-brand-700 hover:text-brand-800 focus:outline-none focus-visible:underline"
            >
              View progress →
            </a>
            <a
              href="/student/learning-path"
              className="text-xs font-medium text-brand-700 hover:text-brand-800 focus:outline-none focus-visible:underline"
            >
              View learning path →
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
