import { useState } from 'react';
import { apiClient } from '@/api/client';
import { useClassInsights } from './useClassInsights';
import type { ClassInsight } from './useClassInsights';
import { Button, ResponsiveTable, type ResponsiveColumn } from '@/shared/ui';
import { useI18n, type LocaleKey } from '@/shared/i18n';

const STATUS_CONFIG: Record<ClassInsight['insight_type'], { dot: string; labelKey: LocaleKey }> = {
  struggling: { dot: 'bg-rose-500', labelKey: 'teacher.statusStruggling' },
  at_risk: { dot: 'bg-amber-400', labelKey: 'teacher.statusAtRisk' },
  proficient: { dot: 'bg-emerald-500', labelKey: 'teacher.statusProficient' },
};

const triggerClassInsights = async (subjectRoomId: number): Promise<void> => {
  await apiClient.post('/ai/trigger/class/', { subject_room_id: subjectRoomId });
};

interface Props {
  subjectRoomId: number;
}

export const ClassHealthPanel = ({ subjectRoomId }: Props) => {
  const { t, locale } = useI18n();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);

  const { data: insights, isLoading, refetch } = useClassInsights(subjectRoomId, isExpanded);

  const columns: ResponsiveColumn<ClassInsight>[] = [
    {
      key: 'chapter',
      header: t('teacher.thChapter'),
      primary: true,
      cell: (insight) => <span className="font-medium text-ink-800">{insight.chapter_name}</span>,
    },
    {
      key: 'avg',
      header: t('teacher.thAvg'),
      align: 'right',
      cell: (insight) => (
        <span className="text-ink-600">{Math.round(insight.class_avg_score * 100)}%</span>
      ),
    },
    {
      key: 'struggling',
      header: t('teacher.thStruggling'),
      align: 'right',
      cell: (insight) => (
        <span className="text-ink-500">
          {insight.students_struggling}/{insight.students_assessed}
        </span>
      ),
    },
    {
      key: 'status',
      header: t('teacher.thStatus'),
      align: 'right',
      cell: (insight) => {
        const cfg = STATUS_CONFIG[insight.insight_type];
        return (
          <span className="inline-flex items-center gap-1">
            <span aria-hidden className={`inline-block h-2 w-2 rounded-full ${cfg.dot}`} />
            <span className="text-ink-600">{t(cfg.labelKey)}</span>
          </span>
        );
      },
    },
  ];

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
        className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-ink-500 transition-colors hover:text-ink-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        <span>{t('teacher.classHealth')}</span>
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
            <p className="py-2 text-xs text-ink-400">{t('teacher.loadingClassHealth')}</p>
          )}

          {!isLoading && (!insights || insights.length === 0) && (
            <div className="py-2 text-xs text-ink-400">
              {t('teacher.noClassHealth')}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={isTriggering}
                className="ml-2"
              >
                {isTriggering ? t('teacher.computing') : t('teacher.refresh')}
              </Button>
            </div>
          )}

          {insights && insights.length > 0 && (
            <>
              <ResponsiveTable
                aria-label={t('teacher.classHealth')}
                rows={insights}
                rowKey={(insight) => insight.id}
                columns={columns}
              />
              <div className="mt-2 flex items-center justify-between">
                <p className="text-xs text-ink-400">
                  {t('teacher.lastUpdated', {
                    datetime: new Date(insights[0].generated_at).toLocaleString(
                      locale === 'hi' ? 'hi-IN' : 'en-IN',
                      { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' },
                    ),
                  })}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isTriggering}
                >
                  {isTriggering ? t('teacher.computing') : t('teacher.refresh')}
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
