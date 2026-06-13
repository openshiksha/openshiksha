import { useNavigate } from 'react-router-dom';
import type { Assignment } from '@/types/index';
import { useT, type LocaleKey } from '@/shared/i18n';
import { bucketize, type Bucket } from './needsAttention';

const toneClass: Record<Bucket['tone'], string> = {
  rose: 'border-rose-200 bg-rose-50 text-rose-900 hover:border-rose-300',
  amber: 'border-amber-200 bg-amber-50 text-amber-900 hover:border-amber-300',
  sky: 'border-sky-200 bg-sky-50 text-sky-900 hover:border-sky-300',
};

// Bucket labels are stable identifiers (also used in data-testids); the
// user-facing chip text comes from the locale files.
const bucketKey: Record<string, LocaleKey> = {
  overdue: 'teacher.bucketOverdue',
  ungraded: 'teacher.bucketUngraded',
  'low completion': 'teacher.bucketLowCompletion',
};

interface Props {
  assignments: Assignment[] | undefined;
}

export const NeedsAttentionPanel = ({ assignments }: Props) => {
  const navigate = useNavigate();
  const t = useT();
  if (!assignments || assignments.length === 0) return null;

  const buckets = bucketize(assignments).filter((b) => b.items.length > 0);
  if (buckets.length === 0) return null;

  const total = buckets.reduce((sum, b) => sum + b.items.length, 0);

  return (
    <section
      aria-label="Needs attention"
      className="rounded-xl border border-ink-100 bg-paper p-4 shadow-sm"
      data-testid="needs-attention"
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-500">
        {t('teacher.needsAttention', { count: total })}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {buckets.map((bucket) => {
          const first = [...bucket.items].sort((a, b) => a.due_at.localeCompare(b.due_at))[0];
          return (
            <button
              key={bucket.label}
              type="button"
              onClick={() => navigate(`/teacher/assignments/${first.id}`)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${toneClass[bucket.tone]}`}
              data-testid={`needs-attention-${bucket.label.replace(/\s/g, '-')}`}
            >
              {t(bucketKey[bucket.label], { count: bucket.items.length })}
            </button>
          );
        })}
      </div>
    </section>
  );
};
