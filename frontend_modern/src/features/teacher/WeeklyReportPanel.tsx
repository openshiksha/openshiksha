import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useWeeklyReport } from './useWeeklyReport';
import { AIBadge, Button, Skeleton, isAIStub } from '@/shared/ui';
import { useI18n, type Locale } from '@/shared/i18n';

const triggerWeeklyReport = async (subjectRoomId: number): Promise<void> => {
  await apiClient.post('/ai/weekly-reports/generate/', { subject_room_id: subjectRoomId });
};

const formatDate = (iso: string, locale: Locale): string =>
  new Date(iso).toLocaleDateString(locale === 'hi' ? 'hi-IN' : 'en-IN', {
    day: 'numeric',
    month: 'short',
  });

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
  const { t, locale } = useI18n();
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

  const isStub = isAIStub(report?.model_used);

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-ink-500 transition-colors hover:text-ink-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        <span>{t('teacher.weeklySummary')}</span>
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
              {t('teacher.weeklyLoadError')}{' '}
              <button
                type="button"
                onClick={() => void refetch()}
                className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
              >
                {t('explanation.retry')}
              </button>
            </p>
          )}

          {!isLoading && !isError && !report && (
            <div className="py-2 text-xs text-ink-400">
              {t('teacher.noWeeklySummary')}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="ml-2"
              >
                {isGenerating ? t('teacher.generating') : t('teacher.generate')}
              </Button>
            </div>
          )}

          {genError && (
            <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
              {t('teacher.weeklyGenError')}
            </p>
          )}

          {!isLoading && !isError && report && (
            <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs font-semibold text-brand-800">
                  {t('teacher.weekOf', {
                    start: formatDate(report.week_start, locale),
                    end: formatDate(report.week_end, locale),
                  })}
                </p>
                <AIBadge modelUsed={report.model_used} stubLabel="Auto-summary" />
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-700">
                {report.summary_text}
              </p>
              {isStub && (
                <p className="mt-1.5 text-xs text-ink-400">{t('teacher.stubSummaryNote')}</p>
              )}

              <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-500">
                <span>
                  {t('teacher.practisedRatio', {
                    active: report.active_students,
                    total: report.total_students,
                  })}
                </span>
                <span>
                  {t(report.ticks_recorded === 1 ? 'teacher.questionsCountOne' : 'teacher.questionsCountMany', {
                    count: report.ticks_recorded,
                  })}
                </span>
                <span>{t('teacher.avgPct', { pct: Math.round(report.class_avg_score * 100) })}</span>
              </div>

              {report.struggling_chapters.length > 0 && (
                <p className="mt-2 text-xs text-ink-600">
                  <span className="font-semibold text-rose-700">{t('teacher.needsWork')}</span>{' '}
                  {report.struggling_chapters.map((c) => c.chapter_name).join(', ')}
                </p>
              )}
              {report.strong_chapters.length > 0 && (
                <p className="mt-0.5 text-xs text-ink-600">
                  <span className="font-semibold text-emerald-700">{t('teacher.strong')}</span>{' '}
                  {report.strong_chapters.map((c) => c.chapter_name).join(', ')}
                </p>
              )}

              <div className="mt-2.5 flex items-center justify-between">
                <p className="text-xs text-ink-400">
                  {t('teacher.generatedOn', { date: formatDate(report.generated_at, locale) })}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                >
                  {isGenerating ? t('teacher.regenerating') : t('teacher.regenerate')}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
