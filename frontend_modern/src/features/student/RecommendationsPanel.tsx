import { Link } from 'react-router-dom';
import { Badge, Skeleton } from '@/shared/ui';
import { useRecommendations } from './useRecommendations';
import { usePracticePlan } from './usePracticePlan';

// ContentRecommendation priority semantics: 1=urgent, 2=high, 3=medium, 4=low.
const PRIORITY_TONE: Record<number, 'urgent' | 'attention' | 'brand' | 'neutral'> = {
  1: 'urgent',
  2: 'attention',
  3: 'brand',
  4: 'neutral',
};

export const RecommendationsPanel = () => {
  const { data: recommendations, isLoading, isError } = useRecommendations();
  const { data: plan } = usePracticePlan();

  // On a failed fetch the panel steps aside rather than stacking another error
  // banner on the dashboard — the assignments list already surfaces
  // connectivity problems prominently.
  if (isError) return null;

  if (isLoading) {
    return (
      <div className="os-card border-brand-200 p-5">
        <Skeleton w="w-48" h="h-5" className="mb-4" />
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex items-center justify-between gap-3 py-2">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <Skeleton w="w-16" h="h-5" rounded="rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton w="w-2/3" h="h-4" />
                  <Skeleton w="w-1/2" h="h-3" />
                </div>
              </div>
              <Skeleton w="w-10" h="h-4" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="os-card p-5">
        <h2 className="text-base font-display font-semibold text-ink-900">
          What to Practice Next
        </h2>
        <p className="text-sm text-ink-500 mt-1">
          No suggestions yet — answer a few assignment questions and we&apos;ll point you to the
          chapters worth revisiting.
        </p>
      </div>
    );
  }

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
              <Badge tone={PRIORITY_TONE[rec.priority] ?? 'brand'} className="mt-0.5 shrink-0">
                {rec.priority_display.toUpperCase()}
              </Badge>
              <div className="min-w-0">
                <p className="text-sm font-medium text-ink-900 truncate">{rec.chapter_name}</p>
                <p className="text-xs text-ink-500 mt-0.5">{rec.reason_display}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-semibold text-ink-700">
                  {Math.round(rec.score_snapshot * 100)}%
                </p>
                <p className="text-xs text-ink-400">your score</p>
              </div>
              <Link
                to={`/student/browse/chapter/${rec.chapter}`}
                className="text-xs font-semibold text-brand-700 hover:text-white border border-brand-200 rounded-full px-3 py-1 hover:bg-brand-600 hover:border-brand-600 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
              >
                Practice
              </Link>
            </div>
          </div>
        ))}
      </div>

      {plan && (
        <div className="mt-4 pt-3 border-t border-ink-100 flex items-center justify-between">
          <span className="text-xs text-ink-500">
            {plan.recommendations.length} topic{plan.recommendations.length !== 1 ? 's' : ''} in
            today&apos;s plan
          </span>
          <div className="flex items-center gap-3">
            <Link
              to="/student/proficiency"
              className="text-xs font-medium text-brand-700 hover:text-brand-800 focus:outline-none focus-visible:underline"
            >
              View progress →
            </Link>
            <Link
              to="/student/learning-path"
              className="text-xs font-medium text-brand-700 hover:text-brand-800 focus:outline-none focus-visible:underline"
            >
              View learning path →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
