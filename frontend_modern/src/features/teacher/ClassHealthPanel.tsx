import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useClassInsights } from './useClassInsights';
import type { ClassInsight } from './useClassInsights';
import { Button } from '@/shared/ui';

const STATUS_CONFIG: Record<ClassInsight['insight_type'], { dot: string; label: string }> = {
  struggling: { dot: 'bg-rose-500', label: 'Struggling' },
  at_risk: { dot: 'bg-amber-400', label: 'At Risk' },
  proficient: { dot: 'bg-emerald-500', label: 'Proficient' },
};

const triggerClassInsights = async (subjectRoomId: number): Promise<void> => {
  await apiClient.post('/ai/trigger/class/', { subject_room_id: subjectRoomId });
};

interface Props {
  subjectRoomId: number;
}

export const ClassHealthPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);

  const { data: insights, isLoading, refetch } = useClassInsights(subjectRoomId, isExpanded);

  const handleRefresh = async () => {
    setIsTriggering(true);
    try {
      await triggerClassInsights(subjectRoomId);
      setTimeout(() => {
        refetch();
        setIsTriggering(false);
      }, 2000);
    } catch {
      setIsTriggering(false);
    }
  };

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-ink-500 transition-colors hover:text-ink-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        <span>Class Health</span>
        <span
          className={`transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`}
          aria-hidden
        >
          ▾
        </span>
      </button>

      {isExpanded && (
        <div className="mt-3">
          {isLoading && (
            <p className="py-2 text-xs text-ink-400">Loading class health data…</p>
          )}

          {!isLoading && (!insights || insights.length === 0) && (
            <div className="py-2 text-xs text-ink-400">
              No class health data yet. Insights appear after students complete assignments.
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={isTriggering}
                className="ml-2"
              >
                {isTriggering ? 'Computing…' : 'Refresh'}
              </Button>
            </div>
          )}

          {insights && insights.length > 0 && (
            <>
              <div className="-mx-1 overflow-x-auto">
              <table className="w-full min-w-[22rem] text-xs">
                <thead>
                  <tr className="border-b border-ink-100 text-ink-500">
                    <th className="pb-1.5 text-left font-display font-semibold">Chapter</th>
                    <th className="pb-1.5 text-right font-display font-semibold">Avg</th>
                    <th className="pb-1.5 text-right font-display font-semibold">Struggling</th>
                    <th className="pb-1.5 text-right font-display font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {insights.map((insight) => {
                    const cfg = STATUS_CONFIG[insight.insight_type];
                    return (
                      <tr
                        key={insight.id}
                        className="border-b border-ink-50 last:border-0"
                      >
                        <td className="py-1.5 font-medium text-ink-800">
                          {insight.chapter_name}
                        </td>
                        <td className="py-1.5 text-right text-ink-600">
                          {Math.round(insight.class_avg_score * 100)}%
                        </td>
                        <td className="py-1.5 text-right text-ink-500">
                          {insight.students_struggling}/{insight.students_assessed}
                        </td>
                        <td className="py-1.5 text-right">
                          <span className="inline-flex items-center gap-1">
                            <span
                              aria-hidden
                              className={`inline-block h-2 w-2 rounded-full ${cfg.dot}`}
                            />
                            <span className="text-ink-600">{cfg.label}</span>
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <p className="text-xs text-ink-400">
                  Last updated:{' '}
                  {new Date(insights[0].generated_at).toLocaleString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isTriggering}
                >
                  {isTriggering ? 'Computing…' : 'Refresh'}
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
