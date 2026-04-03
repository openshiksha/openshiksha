import { isPast, parseISO, differenceInDays } from 'date-fns';
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
      (a) => !a.my_submission?.submitted_at && isPast(parseISO(a.due_at))
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
  const groups = groupAssignments(assignments);

  if (assignments.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">📚</div>
        <h3 className="text-lg font-medium text-gray-700">No assignments yet</h3>
        <p className="text-gray-400 mt-1">Your teacher will assign some soon. Check back later!</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {groups.overdue.length > 0 && (
        <Section title="Overdue" count={groups.overdue.length} accent="red">
          {groups.overdue.map((a) => <AssignmentCard key={a.id} assignment={a} />)}
        </Section>
      )}

      {groups.dueSoon.length > 0 && (
        <Section title="Due Soon" count={groups.dueSoon.length} accent="amber">
          {groups.dueSoon.map((a) => <AssignmentCard key={a.id} assignment={a} />)}
        </Section>
      )}

      {groups.upcoming.length > 0 && (
        <Section title="Upcoming" count={groups.upcoming.length} accent="blue">
          {groups.upcoming.map((a) => <AssignmentCard key={a.id} assignment={a} />)}
        </Section>
      )}

      {groups.completed.length > 0 && (
        <Section title="Completed" count={groups.completed.length} accent="green">
          {groups.completed.map((a) => <AssignmentCard key={a.id} assignment={a} />)}
        </Section>
      )}
    </div>
  );
};

interface SectionProps {
  title: string;
  count: number;
  accent: 'red' | 'amber' | 'blue' | 'green';
  children: React.ReactNode;
}

const ACCENT_COLORS = {
  red: 'text-red-600 bg-red-50',
  amber: 'text-amber-600 bg-amber-50',
  blue: 'text-blue-600 bg-blue-50',
  green: 'text-green-600 bg-green-50',
};

const Section = ({ title, count, accent, children }: SectionProps) => (
  <div>
    <div className="flex items-center gap-2 mb-3">
      <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">{title}</h2>
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ACCENT_COLORS[accent]}`}>
        {count}
      </span>
    </div>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {children}
    </div>
  </div>
);
