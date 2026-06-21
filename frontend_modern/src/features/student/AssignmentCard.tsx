import { formatDistanceToNow, isPast, parseISO } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { Badge, Button } from '@/shared/ui';
import { useI18n } from '@/shared/i18n';
import { dateFnsLocaleFor } from '@/shared/i18n/dateFnsLocale';
import type { Assignment } from '@/types/index';

interface AssignmentCardProps {
  assignment: Assignment;
}

export const AssignmentCard = ({ assignment }: AssignmentCardProps) => {
  const navigate = useNavigate();
  const { t, locale } = useI18n();
  const dateLocale = dateFnsLocaleFor(locale);
  const { problem_set, due_at, my_submission } = assignment;
  const dueDate = parseISO(due_at);
  const isOverdue = isPast(dueDate);
  const isSubmitted = !!my_submission?.submitted_at;
  const completion = my_submission?.completion ?? 0;
  const score = my_submission?.score;

  const dueDateLabel = isOverdue
    ? t('assignment.overdueBy', { distance: formatDistanceToNow(dueDate, { locale: dateLocale }) })
    : t('assignment.dueIn', {
        distance: formatDistanceToNow(dueDate, { addSuffix: true, locale: dateLocale }),
      });

  // Submitted assignments surface *when* they were submitted instead of the
  // due date — once you've turned it in, the due date is irrelevant and the
  // student wants to know "did I do this recently?" at a glance.
  const submittedLabel =
    isSubmitted && my_submission?.submitted_at
      ? t('assignment.submittedAgo', {
          distance: formatDistanceToNow(parseISO(my_submission.submitted_at), {
            addSuffix: true,
            locale: dateLocale,
          }),
        })
      : t('assignment.submitted');

  const cta = isSubmitted
    ? t('assignment.ctaReview')
    : completion > 0
      ? t('assignment.ctaContinue')
      : t('assignment.ctaStart');

  return (
    <div
      className={`os-card w-full min-w-0 p-5 hover:shadow-md transition-shadow motion-reduce:transition-none ${
        // Submitted cards get a subtle emerald edge so the difference reads
        // at a glance in a mixed list, without leaning on color alone (the
        // "Submitted" label + score badge + ghost CTA still carry the
        // signal for users with reduced color vision).
        isSubmitted ? 'border-emerald-200/80 bg-emerald-50/30' : ''
      }`}
    >
      <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-xs font-semibold text-brand-700 uppercase tracking-wide">
              {problem_set.subject.name}
            </p>
            {problem_set.is_remedial && (
              <Badge tone="attention">{t('assignment.remedialBadge')}</Badge>
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
            <span>{t('assignment.progress')}</span>
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

      <div className="flex min-w-0 flex-col gap-3 mt-4 sm:flex-row sm:items-center sm:justify-between">
        <span
          className={`min-w-0 text-xs ${
            isSubmitted
              ? 'text-emerald-700 font-medium'
              : isOverdue
                ? 'text-rose-600 font-medium'
                : 'text-ink-400'
          }`}
        >
          {isSubmitted ? submittedLabel : dueDateLabel}
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
