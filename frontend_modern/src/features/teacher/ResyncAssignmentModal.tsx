import { useEffect } from 'react';
import { LoadingSpinner } from '@/shared/ui';
import { useResyncPreview, useApplyResync } from './useAssignmentResync';

interface Props {
  assignmentId: number;
  open: boolean;
  onClose: () => void;
  onApplied?: () => void;
}

/**
 * AIV-6: re-sync confirmation modal.
 *
 * Opens off the drift banner on `TeacherAssignmentDetailPage`. Fetches the
 * blast-radius preview from the backend, summarises what would change (added /
 * removed questions, answer changes, content-only changes, how many graded
 * submissions get re-queued), and only mutates state when the teacher confirms.
 * Nothing about this surface is automatic — the assignment's snapshot is the
 * source of truth until they click Apply.
 */
export function ResyncAssignmentModal({ assignmentId, open, onClose, onApplied }: Props) {
  const preview = useResyncPreview(assignmentId, open);
  const apply = useApplyResync(assignmentId);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = original;
    };
  }, [open, onClose]);

  if (!open) return null;

  const diff = preview.data?.diff;
  const affected = preview.data?.affected;
  const hasDrift = preview.data?.has_drift ?? false;
  const regradeCount = affected?.regrade_on_apply ?? 0;

  const handleApply = async () => {
    await apply.mutateAsync();
    onApplied?.();
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resync-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 px-4 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg overflow-hidden rounded-xl bg-paper shadow-lift">
        <div className="border-b border-ink-100 px-6 py-4">
          <h2 id="resync-title" className="font-display text-lg font-semibold text-ink-900">
            Update this assignment to the latest content?
          </h2>
          <p className="mt-1 text-xs text-ink-500">
            Re-snapshots from the live set. Reversible from this page.
          </p>
        </div>

        <div className="space-y-4 px-6 py-5">
          {preview.isLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="md" />
            </div>
          ) : preview.isError || !preview.data ? (
            <p className="text-sm text-red-700">Couldn't load the preview. Try again.</p>
          ) : !hasDrift ? (
            <p className="text-sm text-ink-600">
              The snapshot already matches the live set — there's nothing to re-sync.
            </p>
          ) : (
            <>
              <DiffSummary diff={diff!} />
              <div
                className={`rounded-lg border px-3 py-2 text-sm ${
                  regradeCount > 0
                    ? 'border-amber-200 bg-amber-50 text-amber-900'
                    : 'border-ink-100 bg-ink-50 text-ink-700'
                }`}
                data-testid="resync-regrade-note"
              >
                {regradeCount > 0 ? (
                  <>
                    <strong>{regradeCount}</strong> graded submission{regradeCount === 1 ? '' : 's'}{' '}
                    will be <strong>re-graded</strong> against the new answer key. Some students may
                    end up with different scores.
                  </>
                ) : (
                  <>No graded submissions will be re-graded — only what students see is changing.</>
                )}
              </div>
            </>
          )}
          {apply.isError && (
            <p className="text-sm text-red-700">The re-sync failed. Try again.</p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-ink-100 bg-ink-50/60 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-ink-200 bg-white px-3 py-1.5 text-sm font-medium text-ink-700 hover:bg-ink-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleApply}
            disabled={!hasDrift || preview.isLoading || apply.isPending}
            data-testid="resync-apply"
            className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {apply.isPending
              ? 'Updating…'
              : regradeCount > 0
                ? `Update and re-grade ${regradeCount}`
                : 'Update assignment'}
          </button>
        </div>
      </div>
    </div>
  );
}

function DiffSummary({
  diff,
}: {
  diff: NonNullable<ReturnType<typeof useResyncPreview>['data']>['diff'];
}) {
  const lines: string[] = [];
  if (diff.questions_added.length)
    lines.push(`${diff.questions_added.length} question${diff.questions_added.length === 1 ? '' : 's'} added`);
  if (diff.questions_removed.length)
    lines.push(`${diff.questions_removed.length} question${diff.questions_removed.length === 1 ? '' : 's'} removed`);
  if (diff.answer_changes.length)
    lines.push(`${diff.answer_changes.length} answer${diff.answer_changes.length === 1 ? '' : 's'} changed`);
  if (diff.content_changes.length)
    lines.push(
      `${diff.content_changes.length} other content edit${diff.content_changes.length === 1 ? '' : 's'} (prompts, options, widgets)`,
    );
  if (!lines.length) return null;
  return (
    <ul data-testid="resync-diff-summary" className="list-disc space-y-1 pl-5 text-sm text-ink-800">
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}
