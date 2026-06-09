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
interface EditSafetyBannerProps {
  assignedCount: number;
  hasGradedSubmissions: boolean;
  /** "this question" or "this problem set". */
  noun?: string;
}

export function EditSafetyBanner({
  assignedCount,
  hasGradedSubmissions,
  noun = 'this question',
}: EditSafetyBannerProps) {
  if (!assignedCount || assignedCount <= 0) return null;

  const countLabel =
    assignedCount === 1 ? '1 assignment' : `${assignedCount} assignments`;

  return (
    <div
      role="status"
      className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
      data-testid="edit-safety-banner"
    >
      <p className="font-semibold">
        {noun.charAt(0).toUpperCase() + noun.slice(1)} is used in {countLabel}.
      </p>
      <p className="mt-1 text-amber-800">
        {hasGradedSubmissions ? (
          <>
            Your edits apply to <strong>future</strong> assignments only —
            existing ones keep exactly what students were given and were graded
            against.
          </>
        ) : (
          <>
            Your edits apply to <strong>future</strong> assignments only —
            existing ones keep exactly what students were given.
          </>
        )}
      </p>
    </div>
  );
}
