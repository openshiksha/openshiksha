import { useRecommendations } from './useRecommendations';
import { usePracticePlan } from './usePracticePlan';

const PRIORITY_BADGE: Record<number, string> = {
  1: 'bg-red-100 text-red-800 border border-red-300',
  2: 'bg-orange-100 text-orange-800 border border-orange-300',
  3: 'bg-yellow-100 text-yellow-800 border border-yellow-300',
  4: 'bg-blue-100 text-blue-800 border border-blue-300',
};

export const RecommendationsPanel = () => {
  const { data: recommendations, isLoading } = useRecommendations();
  const { data: plan } = usePracticePlan();

  if (isLoading) return null;
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-indigo-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">What to Practice Next</h2>
        {plan && (
          <span className="text-xs text-gray-500">
            Today&apos;s plan: ~{plan.estimated_minutes} min
          </span>
        )}
      </div>

      <div className="space-y-3">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="flex items-start justify-between gap-3 py-2 border-b border-gray-100 last:border-0"
          >
            <div className="flex items-start gap-3 min-w-0">
              <span
                className={`mt-0.5 shrink-0 text-xs font-semibold px-2 py-0.5 rounded ${PRIORITY_BADGE[rec.priority] ?? PRIORITY_BADGE[3]}`}
              >
                {rec.priority_display.toUpperCase()}
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{rec.chapter_name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{rec.reason_display}</p>
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="text-sm font-semibold text-gray-700">
                {Math.round(rec.score_snapshot * 100)}%
              </p>
            </div>
          </div>
        ))}
      </div>

      {plan && (
        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            {plan.recommendations.length} topic{plan.recommendations.length !== 1 ? 's' : ''} in today&apos;s plan
          </span>
          <div className="flex items-center gap-3">
            <a
              href="/student/proficiency"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
            >
              View progress →
            </a>
            <a
              href="/student/learning-path"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
            >
              View learning path →
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
