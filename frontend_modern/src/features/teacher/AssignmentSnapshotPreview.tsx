import { useState } from 'react';
import { Link } from 'react-router-dom';
import { QuestionCard } from '../student/QuestionCard';
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
 */
interface Props {
  problemSet: ProblemSetWithQuestions;
  snapshotDrift: boolean;
}

export function AssignmentSnapshotPreview({ problemSet, snapshotDrift }: Props) {
  const [open, setOpen] = useState(false);
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
    </section>
  );
}
