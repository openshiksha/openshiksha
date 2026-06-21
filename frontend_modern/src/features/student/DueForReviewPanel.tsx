import { Link } from 'react-router-dom';
import { Skeleton } from '@/shared/ui';
import { useT, type Translate } from '@/shared/i18n';
import { useSpacedRepetitionDue } from './useSpacedRepetitionDue';
import type { SRSEntry } from './useSpacedRepetitionDue';

const getToday = () => new Date().toISOString().slice(0, 10);

type Urgency = 'overdue' | 'today' | 'soon';

const getUrgency = (nextReviewDate: string): Urgency => {
  const today = getToday();
  if (nextReviewDate < today) return 'overdue';
  if (nextReviewDate === today) return 'today';
  return 'soon';
};

const URGENCY_STYLES: Record<Urgency, { dot: string; text: string; bg: string }> = {
  overdue: { dot: 'bg-rose-500', text: 'text-rose-700', bg: 'bg-rose-50' },
  today: { dot: 'bg-amber-500', text: 'text-amber-800', bg: 'bg-amber-50' },
  soon: { dot: 'bg-brand-400', text: 'text-brand-700', bg: '' },
};

const dueLabelFor = (t: Translate, urgency: Urgency, nextReviewDate: string): string =>
  urgency === 'overdue'
    ? t('dueReview.overdueSince', { date: nextReviewDate })
    : urgency === 'today'
      ? t('dueReview.statusToday')
      : t('dueReview.dueOn', { date: nextReviewDate });

const SRSRow = ({ entry }: { entry: SRSEntry }) => {
  const t = useT();
  const urgency = getUrgency(entry.next_review_date);
  const style = URGENCY_STYLES[urgency];
  const dueLabel = dueLabelFor(t, urgency, entry.next_review_date);

  return (
    <div className={`flex items-center justify-between py-2.5 px-3 rounded-lg ${style.bg}`}>
      <div className="flex items-center gap-2 min-w-0">
        <span className={`shrink-0 w-2 h-2 rounded-full ${style.dot}`} />
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-900 truncate">{entry.chapter_name}</p>
          <p className={`text-xs ${style.text}`}>{dueLabel}</p>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0 ml-3">
        <div className="text-right hidden sm:block">
          <p className="text-xs text-ink-500">
            {t('dueReview.interval', { days: entry.interval_days })}
          </p>
          <p className="text-xs text-ink-400">
            {t('dueReview.reviewedTimes', { count: entry.repetitions })}
          </p>
        </div>
        <Link
          to={`/student/srs-drill/${entry.id}`}
          className="text-xs font-semibold text-brand-700 hover:text-white border border-brand-200 rounded-full px-3 py-1 hover:bg-brand-600 hover:border-brand-600 transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          {t('common.practice')}
        </Link>
      </div>
    </div>
  );
};

export const DueForReviewPanel = () => {
  const t = useT();
  const { data: entries, isLoading, isError } = useSpacedRepetitionDue();

  // On a failed fetch the panel steps aside rather than stacking another error
  // banner on the dashboard — the assignments list already surfaces
  // connectivity problems prominently.
  if (isError) return null;

  if (isLoading) {
    return (
      <div className="os-card border-amber-200 p-5 mt-6">
        <Skeleton w="w-40" h="h-5" className="mb-4" />
        <div className="space-y-1.5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex items-center justify-between gap-3 py-2.5 px-3">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Skeleton w="w-2" h="h-2" rounded="rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton w="w-2/3" h="h-4" />
                  <Skeleton w="w-1/3" h="h-3" />
                </div>
              </div>
              <Skeleton w="w-16" h="h-6" rounded="rounded-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return (
      <div className="os-card p-5 mt-6">
        <h2 className="text-base font-display font-semibold text-ink-900">
          {t('dueReview.title')}
        </h2>
        <p className="text-sm text-ink-500 mt-1">{t('dueReview.emptyDescription')}</p>
      </div>
    );
  }

  const sorted = [...entries].sort((a, b) =>
    a.next_review_date.localeCompare(b.next_review_date),
  );
  const overdueCount = sorted.filter((e) => getUrgency(e.next_review_date) === 'overdue').length;

  return (
    <div className="os-card border-amber-200 p-5 mt-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-display font-semibold text-ink-900">
          {t('dueReview.title')}
          {overdueCount > 0 && (
            <span className="ml-2 text-xs font-semibold bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full">
              {t('dueReview.overdueCount', { count: overdueCount })}
            </span>
          )}
        </h2>
        <span className="text-xs text-ink-400">
          {t(entries.length === 1 ? 'common.topicsOne' : 'common.topicsMany', {
            count: entries.length,
          })}
        </span>
      </div>
      <div className="space-y-1.5">
        {sorted.slice(0, 5).map((e) => (
          <SRSRow key={e.id} entry={e} />
        ))}
        {entries.length > 5 && (
          <p className="text-xs text-center text-ink-400 pt-1">
            {t('dueReview.moreTopics', { count: entries.length - 5 })}
          </p>
        )}
      </div>
      <p className="text-xs text-ink-400 mt-3 pt-2 border-t border-ink-100">
        {t('dueReview.footer')}
      </p>
    </div>
  );
};
