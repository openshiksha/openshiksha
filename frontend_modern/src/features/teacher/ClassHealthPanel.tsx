import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useClassInsights } from './useClassInsights';
import type { ClassInsight } from './useClassInsights';

const STATUS_CONFIG: Record<ClassInsight['insight_type'], { dot: string; label: string }> = {
  struggling: { dot: 'bg-red-500', label: 'Struggling' },
  at_risk: { dot: 'bg-yellow-400', label: 'At Risk' },
  proficient: { dot: 'bg-green-500', label: 'Proficient' },
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
      // Wait a moment then refetch — task is async on server
      setTimeout(() => {
        refetch();
        setIsTriggering(false);
      }, 2000);
    } catch {
      setIsTriggering(false);
    }
  };

  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-800 transition-colors w-full text-left"
      >
        <span>Class Health</span>
        <span className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3">
          {isLoading && (
            <p className="text-xs text-gray-400 py-2">Loading class health data…</p>
          )}

          {!isLoading && (!insights || insights.length === 0) && (
            <div className="text-xs text-gray-400 py-2">
              No class health data yet. Insights appear after students complete assignments.
              <button
                onClick={handleRefresh}
                disabled={isTriggering}
                className="ml-2 text-indigo-500 hover:text-indigo-700 disabled:opacity-50"
              >
                {isTriggering ? 'Computing…' : 'Refresh'}
              </button>
            </div>
          )}

          {insights && insights.length > 0 && (
            <>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-100">
                    <th className="text-left pb-1.5 font-medium">Chapter</th>
                    <th className="text-right pb-1.5 font-medium">Avg</th>
                    <th className="text-right pb-1.5 font-medium">Struggling</th>
                    <th className="text-right pb-1.5 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {insights.map((insight) => {
                    const cfg = STATUS_CONFIG[insight.insight_type];
                    return (
                      <tr key={insight.id} className="border-b border-gray-50 last:border-0">
                        <td className="py-1.5 text-gray-800 font-medium">{insight.chapter_name}</td>
                        <td className="py-1.5 text-right text-gray-600">
                          {Math.round(insight.class_avg_score * 100)}%
                        </td>
                        <td className="py-1.5 text-right text-gray-500">
                          {insight.students_struggling}/{insight.students_assessed}
                        </td>
                        <td className="py-1.5 text-right">
                          <span className="inline-flex items-center gap-1">
                            <span className={`inline-block w-2 h-2 rounded-full ${cfg.dot}`} />
                            <span className="text-gray-600">{cfg.label}</span>
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="mt-2 flex items-center justify-between">
                <p className="text-xs text-gray-400">
                  Last updated:{' '}
                  {new Date(insights[0].generated_at).toLocaleString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                <button
                  onClick={handleRefresh}
                  disabled={isTriggering}
                  className="text-xs text-indigo-500 hover:text-indigo-700 disabled:opacity-50"
                >
                  {isTriggering ? 'Computing…' : 'Refresh'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
