import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useWeeklyReport } from './useWeeklyReport';

const triggerWeeklyReport = async (subjectRoomId: number): Promise<void> => {
  await apiClient.post('/ai/weekly-reports/generate/', { subject_room_id: subjectRoomId });
};

const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

interface Props {
  subjectRoomId: number;
}

export const WeeklyReportPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const { data: report, isLoading, refetch } = useWeeklyReport(subjectRoomId, isExpanded);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await triggerWeeklyReport(subjectRoomId);
      // Generation is async on the server — give it a moment, then refetch.
      setTimeout(() => {
        refetch();
        setIsGenerating(false);
      }, 2500);
    } catch {
      setIsGenerating(false);
    }
  };

  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-800 transition-colors w-full text-left"
      >
        <span>Weekly AI Summary</span>
        <span className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3">
          {isLoading && <p className="text-xs text-gray-400 py-2">Loading weekly summary…</p>}

          {!isLoading && !report && (
            <div className="text-xs text-gray-400 py-2">
              No weekly summary yet. Generate one from this week's practice activity.
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="ml-2 text-indigo-500 hover:text-indigo-700 disabled:opacity-50"
              >
                {isGenerating ? 'Generating…' : 'Generate'}
              </button>
            </div>
          )}

          {!isLoading && report && (
            <div className="rounded-lg bg-indigo-50/60 border border-indigo-100 p-3">
              <p className="text-xs font-medium text-indigo-700">
                Week of {formatDate(report.week_start)} – {formatDate(report.week_end)}
              </p>
              <p className="mt-1.5 text-sm text-gray-700 leading-relaxed">{report.summary_text}</p>

              <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                <span>
                  {report.active_students}/{report.total_students} practised
                </span>
                <span>{report.ticks_recorded} questions</span>
                <span>{Math.round(report.class_avg_score * 100)}% avg</span>
              </div>

              {report.struggling_chapters.length > 0 && (
                <p className="mt-2 text-xs text-gray-600">
                  <span className="font-medium text-red-600">Needs work:</span>{' '}
                  {report.struggling_chapters.map((c) => c.chapter_name).join(', ')}
                </p>
              )}
              {report.strong_chapters.length > 0 && (
                <p className="mt-0.5 text-xs text-gray-600">
                  <span className="font-medium text-green-600">Strong:</span>{' '}
                  {report.strong_chapters.map((c) => c.chapter_name).join(', ')}
                </p>
              )}

              <div className="mt-2.5 flex items-center justify-between">
                <p className="text-xs text-gray-400">
                  Generated {formatDate(report.generated_at)} · {report.model_used}
                </p>
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="text-xs text-indigo-500 hover:text-indigo-700 disabled:opacity-50"
                >
                  {isGenerating ? 'Regenerating…' : 'Regenerate'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
