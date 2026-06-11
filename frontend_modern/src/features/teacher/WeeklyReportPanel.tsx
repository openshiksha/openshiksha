import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useWeeklyReport } from './useWeeklyReport';
import { Badge, Button, Skeleton } from '@/shared/ui';

const triggerWeeklyReport = async (subjectRoomId: number): Promise<void> => {
  await apiClient.post('/ai/weekly-reports/generate/', { subject_room_id: subjectRoomId });
};

const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

// Mirrors the report card layout (title + badge, then summary lines) so the
// expanded section doesn't reflow when the report lands.
const ReportCardSkeleton = () => (
  <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-3">
    <div className="flex items-start justify-between gap-2">
      <Skeleton w="w-1/3" h="h-4" />
      <Skeleton w="w-24" h="h-5" rounded="rounded-full" />
    </div>
    <div className="mt-2 space-y-1.5">
      <Skeleton w="w-full" h="h-3" />
      <Skeleton w="w-full" h="h-3" />
      <Skeleton w="w-2/3" h="h-3" />
    </div>
  </div>
);

interface Props {
  subjectRoomId: number;
}

export const WeeklyReportPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [genError, setGenError] = useState(false);

  const {
    data: report,
    isLoading,
    isError,
    refetch,
  } = useWeeklyReport(subjectRoomId, isExpanded);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenError(false);
    try {
      await triggerWeeklyReport(subjectRoomId);
      setTimeout(() => {
        refetch();
        setIsGenerating(false);
      }, 2500);
    } catch {
      // Surface the failure rather than silently reverting to the empty state —
      // a teacher who clicked "Generate" needs to know it did not work.
      setGenError(true);
      setIsGenerating(false);
    }
  };

  // The provider cascade falls back to a deterministic, data-derived summary when
  // no LLM key is configured. That text is still useful, but we must not present
  // it as genuine AI output (provider-cascade transparency).
  const isStub = report?.model_used === 'stub';

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
          {isLoading && <ReportCardSkeleton />}

          {/* A failed fetch must not masquerade as "no summary yet" — that
              would invite the teacher to regenerate a report that may already
              exist, instead of telling them we couldn't reach the server. */}
          {!isLoading && isError && (
            <p className="py-2 text-xs text-rose-600">
              Couldn&apos;t load the weekly summary just now.{' '}
              <button
                type="button"
                onClick={() => void refetch()}
                className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
              >
                Retry
              </button>
            </p>
          )}

          {!isLoading && !isError && !report && (
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

          {genError && (
            <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
              Couldn't generate the summary just now. Please try again in a moment.
            </p>
          )}

          {!isLoading && !isError && report && (
            <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-semibold text-brand-800">
                  Week of {formatDate(report.week_start)} – {formatDate(report.week_end)}
                </p>
                <Badge tone={isStub ? 'neutral' : 'brand'}>
                  {isStub ? 'Auto-summary' : '✨ AI-generated'}
                </Badge>
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-700">
                {report.summary_text}
              </p>
              {isStub && (
                <p className="mt-1.5 text-xs text-ink-400">
                  AI was unavailable, so this was built directly from your class data.
                </p>
              )}

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
