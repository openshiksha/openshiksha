import { useEffect, useState } from 'react';
import { Badge, Button, Skeleton } from '@/shared/ui';
import { useT, type LocaleKey } from '@/shared/i18n';
import {
  useCalibrationSummary,
  useFlaggedCalibrations,
  useRefreshCalibrations,
  type CalibrationFlag,
  type DifficultyCalibration,
} from './useDifficultyCalibration';

const FLAG_TONE: Record<CalibrationFlag, 'urgent' | 'attention' | 'neutral' | 'success'> = {
  too_hard: 'urgent',
  low_discrimination: 'urgent',
  mislabeled: 'attention',
  too_easy: 'neutral',
  ok: 'success',
};

// Short, teacher-friendly gloss for each flag — why it surfaced and what to check.
const FLAG_HINT: Record<CalibrationFlag, LocaleKey> = {
  too_hard: 'teacher.flagTooHard',
  too_easy: 'teacher.flagTooEasy',
  mislabeled: 'teacher.flagMislabeled',
  low_discrimination: 'teacher.flagLowDiscrimination',
  ok: 'teacher.flagOk',
};

const pct = (v: number): string => `${Math.round(v * 100)}%`;

interface CardProps {
  item: DifficultyCalibration;
}

const CalibrationCard = ({ item }: CardProps) => {
  const t = useT();
  const delta = item.difficulty_delta;
  return (
    <div className="rounded-xl border border-ink-100 bg-paper p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-base text-ink-900 leading-tight truncate">
            {item.question_preview || t('teacher.questionFallback', { id: item.question_id })}
          </p>
          <p className="text-xs text-ink-500 mt-0.5">
            {item.chapter_name} ·{' '}
            {t(item.sample_size === 1 ? 'teacher.studentsCountOne' : 'teacher.studentsCountMany', {
              count: item.sample_size,
            })}{' '}
            · {t('teacher.correctPct', { pct: pct(item.facility_index) })}
          </p>
        </div>
        <Badge tone={FLAG_TONE[item.flag]}>{item.flag_display}</Badge>
      </div>

      <p className="mt-3 text-sm text-ink-700 leading-relaxed">{t(FLAG_HINT[item.flag])}</p>

      <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
        <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
          {t('teacher.authoredDifficulty')} <span className="text-ink-400">{item.declared_difficulty}/5</span>
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
          {t('teacher.observedDifficulty')} <span className="text-ink-400">{item.empirical_difficulty}/5</span>
        </span>
        {delta !== 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
            {delta > 0 ? t('teacher.harderThanLabelled') : t('teacher.easierThanLabelled')}
            <span className="text-ink-400">
              {delta > 0 ? '+' : ''}
              {delta}
            </span>
          </span>
        )}
        {item.discrimination_index !== null && (
          <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
            {t('teacher.discrimination')}
            <span className="text-ink-400">{item.discrimination_index.toFixed(2)}</span>
          </span>
        )}
      </div>
    </div>
  );
};

// Mirrors the CalibrationCard layout so the list doesn't reflow when data lands.
const CalibrationCardSkeleton = () => (
  <div className="rounded-xl border border-ink-100 bg-paper p-4">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <Skeleton w="w-2/3" h="h-5" />
        <Skeleton w="w-1/2" h="h-3" />
      </div>
      <Skeleton w="w-20" h="h-5" rounded="rounded-full" />
    </div>
    <Skeleton w="w-5/6" h="h-3" className="mt-3" />
    <div className="mt-3 flex gap-1.5">
      <Skeleton w="w-28" h="h-5" rounded="rounded-full" />
      <Skeleton w="w-28" h="h-5" rounded="rounded-full" />
      <Skeleton w="w-24" h="h-5" rounded="rounded-full" />
    </div>
  </div>
);

interface Props {
  subjectRoomId: number;
}

/**
 * Teacher AI Assistant — empirical question-quality (item analysis) panel.
 *
 * Surfaces questions whose real classroom performance disagrees with how they
 * were authored: too easy/hard, mis-labelled difficulty, or low discrimination
 * (a mis-keyed-answer smell). Derived purely from grading data — no LLM.
 * Collapsible to keep the dashboard tidy; only the room's teacher sees data.
 * Built on the V2 "Chalk & Unlock" primitives.
 */
export const QuestionQualityPanel = ({ subjectRoomId }: Props) => {
  const t = useT();
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    data: flagged,
    isLoading,
    isError,
    refetch,
  } = useFlaggedCalibrations(subjectRoomId, isExpanded);
  const { data: summary } = useCalibrationSummary(subjectRoomId, isExpanded);
  const refresh = useRefreshCalibrations(subjectRoomId);

  // The "Recalibrating…" confirmation reassures right after a click, but the
  // recalibration runs async, so we can't reliably detect when fresh verdicts
  // land. Clear it on a timer instead of leaving a stale status line forever.
  const refreshSucceeded = refresh.isSuccess;
  const resetRefresh = refresh.reset;
  useEffect(() => {
    if (!refreshSucceeded) return;
    const timer = setTimeout(() => resetRefresh(), 6000);
    return () => clearTimeout(timer);
  }, [refreshSucceeded, resetRefresh]);

  const items = flagged ?? [];

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        aria-expanded={isExpanded}
        className="flex items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-ink-800 transition-colors w-full text-left"
      >
        <span>{t('teacher.questionQuality')}</span>
        {items.length > 0 && <Badge tone="attention">{items.length}</Badge>}
        <span className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {summary && summary.total_calibrated > 0 && (
            <p className="text-xs text-ink-500">
              {t(
                summary.total_calibrated === 1
                  ? 'teacher.calibrationSummaryOne'
                  : 'teacher.calibrationSummaryMany',
                { flagged: summary.flagged, total: summary.total_calibrated },
              )}
            </p>
          )}

          {isLoading && (
            <>
              <CalibrationCardSkeleton />
              <CalibrationCardSkeleton />
            </>
          )}

          {/* A failed fetch must not masquerade as "no questions flagged" —
              that would tell the teacher their question bank is healthy when
              we just couldn't reach the server. */}
          {!isLoading && isError && (
            <p className="text-xs text-rose-600 py-2">
              {t('teacher.qualityLoadError')}{' '}
              <button
                type="button"
                onClick={() => void refetch()}
                className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
              >
                {t('explanation.retry')}
              </button>
            </p>
          )}

          {!isLoading && !isError && items.length === 0 && (
            <div className="text-xs text-ink-500 py-2">{t('teacher.noFlagged')}</div>
          )}

          {!isLoading &&
            !isError &&
            items.map((item) => <CalibrationCard key={item.id} item={item} />)}

          {refresh.isError && (
            <p className="text-xs text-rose-600 pt-1">{t('teacher.recalibrateStartError')}</p>
          )}

          {refresh.isSuccess && (
            <p className="text-xs text-ink-400 pt-1" role="status">
              {t('teacher.recalibrating')}
            </p>
          )}

          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-ink-400">{t('teacher.qualityFootnote')}</p>
            <Button
              variant="ghost"
              size="sm"
              disabled={refresh.isPending}
              onClick={() => refresh.mutate()}
            >
              {refresh.isPending
                ? t('teacher.refreshing')
                : items.length > 0
                  ? t('teacher.refresh')
                  : t('teacher.calibrate')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
