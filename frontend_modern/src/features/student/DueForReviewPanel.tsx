import { Link } from 'react-router-dom';
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

const URGENCY_STYLES: Record<Urgency, { dot: string; text: string; label: string; bg: string }> = {
  overdue: { dot: 'bg-rose-500', text: 'text-rose-700', label: 'Overdue', bg: 'bg-rose-50' },
  today: { dot: 'bg-amber-500', text: 'text-amber-800', label: 'Due today', bg: 'bg-amber-50' },
  soon: { dot: 'bg-brand-400', text: 'text-brand-700', label: 'Coming up', bg: '' },
};

const SRSRow = ({ entry }: { entry: SRSEntry }) => {
  const urgency = getUrgency(entry.next_review_date);
  const style = URGENCY_STYLES[urgency];
  const dueLabel =
    urgency === 'overdue'
      ? `Overdue since ${entry.next_review_date}`
      : urgency === 'today'
        ? 'Due today'
        : `Due ${entry.next_review_date}`;

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
          <p className="text-xs text-ink-500">every {entry.interval_days}d</p>
          <p className="text-xs text-ink-400">{entry.repetitions}× reviewed</p>
        </div>
        <Link
          to={`/student/srs-drill/${entry.id}`}
          className="text-xs font-semibold text-brand-700 hover:text-white border border-brand-200 rounded-full px-3 py-1 hover:bg-brand-600 hover:border-brand-600 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          Practice
        </Link>
      </div>
    </div>
  );
};

export const DueForReviewPanel = () => {
  const { data: entries } = useSpacedRepetitionDue();

  if (!entries || entries.length === 0) return null;

  const sorted = [...entries].sort((a, b) =>
    a.next_review_date.localeCompare(b.next_review_date),
  );
  const overdueCount = sorted.filter((e) => getUrgency(e.next_review_date) === 'overdue').length;

  return (
    <div className="os-card border-amber-200 p-5 mt-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-display font-semibold text-ink-900">
          Due for Review
          {overdueCount > 0 && (
            <span className="ml-2 text-xs font-semibold bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full">
              {overdueCount} overdue
            </span>
          )}
        </h2>
        <span className="text-xs text-ink-400">
          {entries.length} topic{entries.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div className="space-y-1.5">
        {sorted.slice(0, 5).map((e) => (
          <SRSRow key={e.id} entry={e} />
        ))}
        {entries.length > 5 && (
          <p className="text-xs text-center text-ink-400 pt-1">
            +{entries.length - 5} more topics
          </p>
        )}
      </div>
      <p className="text-xs text-ink-400 mt-3 pt-2 border-t border-ink-100">
        Practice your assignments to push review dates forward.
      </p>
    </div>
  );
};
