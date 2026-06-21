/**
 * AIV-3b: non-blocking edit-safety banner.
 *
 * Surfaces on the teacher edit form when the question or problem set is already
 * referenced by one or more assignments. Editing is **safe by construction**
 * (AIV-1/2 snapshot per-assignment content at assign time), so this banner is
 * informational, not a gate — nothing is disabled. Wording is stronger when
 * a graded submission exists, because that's the case where the silent-edit
 * surprise was historically worst.
 */
import { useT } from '@/shared/i18n';

interface EditSafetyBannerProps {
  assignedCount: number;
  hasGradedSubmissions: boolean;
  /** Which thing is being edited — drives the localized headline noun. */
  subject?: 'question' | 'problemSet';
}

export function EditSafetyBanner({
  assignedCount,
  hasGradedSubmissions,
  subject = 'question',
}: EditSafetyBannerProps) {
  const t = useT();
  if (!assignedCount || assignedCount <= 0) return null;

  const single = assignedCount === 1;
  const headlineKey =
    subject === 'problemSet'
      ? single
        ? 'editSafety.usedSetOne'
        : 'editSafety.usedSetMany'
      : single
        ? 'editSafety.usedQuestionOne'
        : 'editSafety.usedQuestionMany';

  return (
    <div
      role="status"
      className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
      data-testid="edit-safety-banner"
    >
      <p className="font-semibold">{t(headlineKey, { count: assignedCount })}</p>
      <p className="mt-1 text-amber-800">
        {t(hasGradedSubmissions ? 'editSafety.bodyGraded' : 'editSafety.body')}
      </p>
    </div>
  );
}
