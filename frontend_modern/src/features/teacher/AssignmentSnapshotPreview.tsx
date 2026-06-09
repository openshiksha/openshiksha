import { useState } from 'react';
import { Link } from 'react-router-dom';
import { QuestionCard } from '../student/QuestionCard';
import { ResyncAssignmentModal } from './ResyncAssignmentModal';
import { useUndoResync } from './useAssignmentResync';
import type { ProblemSetWithQuestions } from '@/types/index';

/**
 * AIV-5: collapsible "what students see" preview embedded on the teacher
 * assignment-detail page. Renders the **frozen snapshot** sourced from
 * ``Assignment.assigned_content`` — the same payload AIV-2b serves to the
 * student. Inputs are locked via ``isSubmitted`` so nothing can be typed.
 *
 * When ``snapshotDrift`` is true the live ``ProblemSet`` has moved past the
 * snapshot; show an amber notice that links to the editable preview so the
 * teacher can compare. The frozen snapshot is what was actually assigned —
 * editing the live set does not retroactively change it (AIV-1/2).
 *
 * AIV-6: the drift banner also offers an **opt-in "Update to latest content"**
 * action that opens ``ResyncAssignmentModal``. When ``hasResyncHistory`` is
 * true (the assignment was re-synced previously) an **Undo last update**
 * affordance appears so the teacher can roll back to the most recent prior
 * snapshot.
 */
interface Props {
  assignmentId: number;
  problemSet: ProblemSetWithQuestions;
  snapshotDrift: boolean;
  /** When true, ``Assignment.snapshot_history`` is non-empty so undo is offered. */
  hasResyncHistory?: boolean;
}

export function AssignmentSnapshotPreview({
  assignmentId,
  problemSet,
  snapshotDrift,
  hasResyncHistory = false,
}: Props) {
  const [open, setOpen] = useState(false);
  const [resyncOpen, setResyncOpen] = useState(false);
  const undo = useUndoResync(assignmentId);
  const questions = problemSet.questions ?? [];

  return (
    <section className="os-card overflow-hidden p-0" data-testid="snapshot-preview">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        data-testid="snapshot-toggle"
        className="flex w-full items-center justify-between gap-3 border-b border-ink-100 px-6 py-4 text-left hover:bg-ink-50"
      >
        <div>
          <h2 className="font-display text-base font-semibold text-ink-900">
            What students see · snapshot
          </h2>
          <p className="mt-0.5 text-xs text-ink-400">
            Frozen at assign time — editing the set later doesn't change this view.
          </p>
        </div>
        <span className="text-sm font-medium text-brand-700">
          {open ? 'Hide' : 'Show'}
        </span>
      </button>

      {snapshotDrift && (
        <div
          role="status"
          data-testid="snapshot-drift-banner"
          className="border-b border-amber-200 bg-amber-50 px-6 py-3 text-sm text-amber-900"
        >
          <p className="font-semibold">The live set has changed since this assignment was given.</p>
          <p className="mt-0.5 text-amber-800">
            What students see and how this assignment grades come from the frozen snapshot above —
            newer assignments will use the updated set.{' '}
            <Link
              to={`/teacher/problem-sets/${problemSet.id}/preview`}
              className="font-semibold underline hover:text-amber-950"
            >
              Compare with the live set
            </Link>
            .
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setResyncOpen(true)}
              data-testid="open-resync-modal"
              className="rounded-md bg-amber-200/80 px-3 py-1 text-xs font-semibold text-amber-950 hover:bg-amber-200"
            >
              Update this assignment…
            </button>
            <span className="text-xs text-amber-800">
              We'll show what changes before anything is applied.
            </span>
          </div>
        </div>
      )}

      {hasResyncHistory && (
        <div
          data-testid="undo-resync-bar"
          className="flex flex-wrap items-center justify-between gap-2 border-b border-ink-100 bg-ink-50/60 px-6 py-2 text-xs text-ink-600"
        >
          <span>This assignment was updated; an earlier snapshot is kept in history.</span>
          <button
            type="button"
            onClick={() => undo.mutate()}
            disabled={undo.isPending}
            data-testid="undo-resync"
            className="rounded-md border border-ink-200 bg-white px-2 py-1 font-medium text-ink-700 hover:bg-ink-100 disabled:opacity-50"
          >
            {undo.isPending ? 'Undoing…' : 'Undo last update'}
          </button>
        </div>
      )}

      {open && (
        <div className="space-y-4 bg-paper px-6 py-5">
          {questions.length === 0 ? (
            <p className="text-sm italic text-ink-400">
              This assignment's snapshot is empty.
            </p>
          ) : (
            questions.map((q, i) => (
              <QuestionCard
                key={q.id}
                question={q}
                questionNumber={i + 1}
                answers={{}}
                onAnswerChange={() => {}}
                isSubmitted
              />
            ))
          )}
        </div>
      )}

      <ResyncAssignmentModal
        assignmentId={assignmentId}
        open={resyncOpen}
        onClose={() => setResyncOpen(false)}
      />
    </section>
  );
}
