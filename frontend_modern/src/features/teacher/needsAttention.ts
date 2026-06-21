import type { Assignment } from '@/types/index';

const LOW_COMPLETION_THRESHOLD = 0.5;

export interface Bucket {
  label: string;
  items: Assignment[];
  tone: 'rose' | 'amber' | 'sky';
}

/**
 * Categorize past-due assignments with explicit precedence:
 * overdue > ungraded > low-completion. Each assignment lands in at most one
 * bucket so counts and links never double-up.
 *
 * - overdue: past due and not all students submitted (completion_rate < 1)
 * - ungraded: past due, fully submitted, but no grades yet
 * - low completion: past due, graded, but completion < 50%
 *
 * Future-dated assignments are skipped entirely.
 */
export const bucketize = (assignments: Assignment[], now: Date = new Date()): Bucket[] => {
  const overdue: Assignment[] = [];
  const ungraded: Assignment[] = [];
  const lowCompletion: Assignment[] = [];

  for (const a of assignments) {
    if (new Date(a.due_at) >= now) continue;
    const completion = a.completion_rate;
    const isPartiallySubmitted = completion !== null && completion < 1;
    if (isPartiallySubmitted) {
      overdue.push(a);
      continue;
    }
    if (a.average_score === null) {
      ungraded.push(a);
      continue;
    }
    if (completion !== null && completion < LOW_COMPLETION_THRESHOLD) {
      lowCompletion.push(a);
    }
  }

  return [
    { label: 'overdue', items: overdue, tone: 'rose' },
    { label: 'ungraded', items: ungraded, tone: 'amber' },
    { label: 'low completion', items: lowCompletion, tone: 'sky' },
  ];
};
