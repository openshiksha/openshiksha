import { isPast, parseISO, differenceInDays } from 'date-fns';
import { EmptyState } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import type { Assignment } from '@/types/index';
import { AssignmentCard } from './AssignmentCard';

interface AssignmentListProps {
  assignments: Assignment[];
}

interface GroupedAssignments {
  overdue: Assignment[];
  dueSoon: Assignment[];
  upcoming: Assignment[];
  completed: Assignment[];
}

function groupAssignments(assignments: Assignment[]): GroupedAssignments {
  const now = new Date();

  return {
    overdue: assignments.filter(
      (a) => !a.my_submission?.submitted_at && isPast(parseISO(a.due_at)),
    ),
    dueSoon: assignments.filter((a) => {
      if (a.my_submission?.submitted_at) return false;
      const due = parseISO(a.due_at);
      if (isPast(due)) return false;
      return differenceInDays(due, now) <= 3;
    }),
    upcoming: assignments.filter((a) => {
      if (a.my_submission?.submitted_at) return false;
      const due = parseISO(a.due_at);
      if (isPast(due)) return false;
      return differenceInDays(due, now) > 3;
    }),
    completed: assignments.filter((a) => !!a.my_submission?.submitted_at),
  };
}

export const AssignmentList = ({ assignments }: AssignmentListProps) => {
  const t = useT();
  const groups = groupAssignments(assignments);

  if (assignments.length === 0) {
    return (
      <EmptyState
        title={t('assignments.emptyTitle')}
        description={t('assignments.emptyDescription')}
      />
    );
  }

  return (
    <div className="space-y-8">
      {groups.overdue.length > 0 && (
        <Section
          title={t('assignments.sectionOverdue')}
          count={groups.overdue.length}
          accent="urgent"
        >
          {groups.overdue.map((a) => (
            <AssignmentCard key={a.id} assignment={a} />
          ))}
        </Section>
      )}

      {groups.dueSoon.length > 0 && (
        <Section
          title={t('assignments.sectionDueSoon')}
          count={groups.dueSoon.length}
          accent="attention"
        >
          {groups.dueSoon.map((a) => (
            <AssignmentCard key={a.id} assignment={a} />
          ))}
        </Section>
      )}

      {groups.upcoming.length > 0 && (
        <Section
          title={t('assignments.sectionUpcoming')}
          count={groups.upcoming.length}
          accent="brand"
        >
          {groups.upcoming.map((a) => (
            <AssignmentCard key={a.id} assignment={a} />
          ))}
        </Section>
      )}

      {groups.completed.length > 0 && (
        <Section
          title={t('assignments.sectionCompleted')}
          count={groups.completed.length}
          accent="success"
        >
          {groups.completed.map((a) => (
            <AssignmentCard key={a.id} assignment={a} />
          ))}
        </Section>
      )}
    </div>
  );
};

type Accent = 'urgent' | 'attention' | 'brand' | 'success';

interface SectionProps {
  title: string;
  count: number;
  accent: Accent;
  children: React.ReactNode;
}

const ACCENT_COLORS: Record<Accent, string> = {
  urgent: 'text-rose-700 bg-rose-50',
  attention: 'text-amber-800 bg-amber-50',
  brand: 'text-brand-700 bg-brand-50',
  success: 'text-emerald-700 bg-emerald-50',
};

const Section = ({ title, count, accent, children }: SectionProps) => (
  <div>
    <div className="flex items-center gap-2 mb-3">
      <h2 className="text-sm font-semibold text-ink-700 uppercase tracking-wider">{title}</h2>
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ACCENT_COLORS[accent]}`}>
        {count}
      </span>
    </div>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{children}</div>
  </div>
);
