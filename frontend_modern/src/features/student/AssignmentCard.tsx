import { formatDistanceToNow, isPast, parseISO } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { Badge, Button } from '@/shared/ui';
import type { Assignment } from '@/types/index';

interface AssignmentCardProps {
  assignment: Assignment;
}

export const AssignmentCard = ({ assignment }: AssignmentCardProps) => {
  const navigate = useNavigate();
  const { problem_set, due_at, my_submission } = assignment;
  const dueDate = parseISO(due_at);
  const isOverdue = isPast(dueDate);
  const isSubmitted = !!my_submission?.submitted_at;
  const completion = my_submission?.completion ?? 0;
  const score = my_submission?.score;

  const dueDateLabel = isOverdue
    ? `Overdue by ${formatDistanceToNow(dueDate)}`
    : `Due ${formatDistanceToNow(dueDate, { addSuffix: true })}`;

  const cta = isSubmitted ? 'Review' : completion > 0 ? 'Continue' : 'Start';

  return (
    <div className="os-card p-5 hover:shadow-md transition-shadow motion-reduce:transition-none">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-xs font-semibold text-brand-700 uppercase tracking-wide">
              {problem_set.subject.name}
            </p>
            {problem_set.is_remedial && (
              <Badge tone="attention">Remedial Practice</Badge>
            )}
          </div>
          <h3 className="font-display font-semibold text-ink-900 truncate">
            {problem_set.title}
          </h3>
          <p className="text-sm text-ink-500 mt-0.5">{problem_set.chapter.name}</p>
        </div>

        {isSubmitted && score !== null && score !== undefined && (
          <div className="flex-shrink-0">
            <Badge
              tone={score >= 0.8 ? 'success' : score >= 0.5 ? 'attention' : 'urgent'}
              className="px-3 py-1 text-sm"
            >
              {Math.round(score * 100)}%
            </Badge>
          </div>
        )}
      </div>

      {/* Progress bar — uses unlock motif: brand fill on warm ink-100 track */}
      {!isSubmitted && completion > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-ink-500 mb-1">
            <span>Progress</span>
            <span>{Math.round(completion * 100)}%</span>
          </div>
          <div className="h-1.5 bg-ink-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all motion-reduce:transition-none"
              style={{ width: `${completion * 100}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4">
        <span
          className={`text-xs ${
            isOverdue && !isSubmitted ? 'text-rose-600 font-medium' : 'text-ink-400'
          }`}
        >
          {isSubmitted ? 'Submitted' : dueDateLabel}
        </span>
        <Button
          variant={isSubmitted ? 'ghost' : 'brand'}
          size="sm"
          className="w-full sm:w-auto"
          onClick={() => navigate(`/student/assignments/${assignment.id}`)}
        >
          {cta}
        </Button>
      </div>
    </div>
  );
};
