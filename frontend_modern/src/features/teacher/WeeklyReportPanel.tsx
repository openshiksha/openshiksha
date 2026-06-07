import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useWeeklyReport } from './useWeeklyReport';
import { Button } from '@/shared/ui';

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
      setTimeout(() => {
        refetch();
        setIsGenerating(false);
      }, 2500);
    } catch {
      setIsGenerating(false);
    }
  };

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-ink-500 transition-colors hover:text-ink-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        <span>Weekly AI Summary</span>
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
            <p className="py-2 text-xs text-ink-400">Loading weekly summary…</p>
          )}

          {!isLoading && !report && (
            <div className="py-2 text-xs text-ink-400">
              No weekly summary yet. Generate one from this week's practice activity.
              <Button
                variant="ghost"
                size="sm"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="ml-2"
              >
                {isGenerating ? 'Generating…' : 'Generate'}
              </Button>
            </div>
          )}

          {!isLoading && report && (
            <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-3">
              <p className="text-xs font-semibold text-brand-800">
                Week of {formatDate(report.week_start)} – {formatDate(report.week_end)}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-700">
                {report.summary_text}
              </p>

              <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-500">
                <span>
                  {report.active_students}/{report.total_students} practised
                </span>
                <span>{report.ticks_recorded} questions</span>
                <span>{Math.round(report.class_avg_score * 100)}% avg</span>
              </div>

              {report.struggling_chapters.length > 0 && (
                <p className="mt-2 text-xs text-ink-600">
                  <span className="font-semibold text-rose-700">Needs work:</span>{' '}
                  {report.struggling_chapters.map((c) => c.chapter_name).join(', ')}
                </p>
              )}
              {report.strong_chapters.length > 0 && (
                <p className="mt-0.5 text-xs text-ink-600">
                  <span className="font-semibold text-emerald-700">Strong:</span>{' '}
                  {report.strong_chapters.map((c) => c.chapter_name).join(', ')}
                </p>
              )}

              <div className="mt-2.5 flex items-center justify-between">
                <p className="text-xs text-ink-400">
                  Generated {formatDate(report.generated_at)}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                >
                  {isGenerating ? 'Regenerating…' : 'Regenerate'}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
