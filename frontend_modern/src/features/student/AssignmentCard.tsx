import { formatDistanceToNow, isPast, parseISO } from 'date-fns';
import { useNavigate } from 'react-router-dom';
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
  const ctaStyle = isSubmitted
    ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    : 'bg-indigo-600 text-white hover:bg-indigo-700';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        {/* Left: Content info */}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-indigo-600 uppercase tracking-wide mb-1">
            {problem_set.subject.name}
          </p>
          <h3 className="font-semibold text-gray-900 truncate">
            {problem_set.title}
          </h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {problem_set.chapter.name}
          </p>
        </div>

        {/* Right: Score badge */}
        {isSubmitted && score !== null && score !== undefined && (
          <div className="flex-shrink-0">
            <div className={`text-sm font-semibold rounded-lg px-3 py-1 ${
              score >= 0.8 ? 'bg-green-100 text-green-700'
              : score >= 0.5 ? 'bg-yellow-100 text-yellow-700'
              : 'bg-red-100 text-red-700'
            }`}>
              {Math.round(score * 100)}%
            </div>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {!isSubmitted && completion > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span>{Math.round(completion * 100)}%</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all"
              style={{ width: `${completion * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer: due date + CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4">
        <span className={`text-xs ${isOverdue && !isSubmitted ? 'text-red-600 font-medium' : 'text-gray-400'}`}>
          {isSubmitted ? 'Submitted' : dueDateLabel}
        </span>
        <button
          onClick={() => navigate(`/student/assignments/${assignment.id}`)}
          className={`w-full sm:w-auto text-sm font-medium px-4 py-2.5 sm:py-1.5 rounded-lg transition-colors ${ctaStyle}`}
        >
          {cta}
        </button>
      </div>
    </div>
  );
};
