import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useProblemSetPreview } from './useProblemSetPreview';
import { useRemoveQuestionFromProblemSet } from './useRemoveQuestionFromProblemSet';
import { QuestionCard } from '../student/QuestionCard';
import { Button, EmptyState, LoadingSpinner } from '@/shared/ui';
import { EditSafetyBanner } from './EditSafetyBanner';

/**
 * Read-only "view as student" preview of a problem set — with an optional
 * **edit mode** (TW-2 / AIV-4).
 *
 * Renders each question through the **same `<QuestionCard>` students use** on
 * the assignment page — correct answers stripped, `{{var}}` substituted, MCQs
 * shuffled. Inputs are locked via `isSubmitted` so nothing can be typed or
 * submitted: a teacher is inspecting, not solving.
 *
 * Edit mode lets the creator remove questions from the live set, jump to the
 * question editor, or jump to the bank to add more. Editing the live set is
 * safe by construction: AIV-1/2 snapshot per-assignment content at assign
 * time, so existing assignments keep exactly what students were given.
 */
export const ProblemSetPreviewPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const setId = id ? Number(id) : null;
  const { data, isLoading, isError } = useProblemSetPreview(setId);
  const removeQuestion = useRemoveQuestionFromProblemSet();
  const [isEditing, setIsEditing] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <EmptyState
          title="Couldn't load this preview"
          description="The problem set may have been removed, or you may not have access to it."
          action={<Button onClick={() => navigate('/teacher')}>Back to dashboard</Button>}
        />
      </div>
    );
  }

  const canEdit = data.created_by_me === true && setId != null;
  const assignedCount = data.assigned_count ?? 0;
  const hasGraded = data.has_graded_submissions ?? false;
  const returnTo = `/teacher/problem-sets/${setId}/preview`;
  // Send the teacher to the question bank, scoped to the set's subject so the
  // first results are relevant; their "Add to set" sheet already drives the
  // add-question API. ``returnTo`` carries them back here after they confirm.
  const addPath = `/teacher/questions?returnTo=${encodeURIComponent(returnTo)}`;

  const handleRemove = (questionId: number) => {
    if (setId == null) return;
    if (
      !window.confirm(
        assignedCount > 0
          ? 'Remove this question from the live set?\n\nExisting assignments keep it — they grade and render the frozen copy.'
          : 'Remove this question from the set?',
      )
    ) {
      return;
    }
    removeQuestion.mutate({ problemSetId: setId, questionId });
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      {/* Mode banner */}
      <div
        className={`flex flex-wrap items-center gap-3 rounded-xl border px-4 py-3 ${
          isEditing
            ? 'border-amber-200 bg-amber-50'
            : 'border-brand-200 bg-brand-50'
        }`}
      >
        <span
          className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
            isEditing ? 'bg-amber-100 text-amber-700' : 'bg-brand-100 text-brand-700'
          }`}
        >
          <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
            <path d="M10 4C5.5 4 2 7.5 1 10c1 2.5 4.5 6 9 6s8-3.5 9-6c-1-2.5-4.5-6-9-6zm0 9a3 3 0 110-6 3 3 0 010 6z" />
          </svg>
        </span>
        <div className="min-w-0 flex-1">
          <p
            className={`text-sm font-semibold ${
              isEditing ? 'text-amber-900' : 'text-brand-900'
            }`}
          >
            {isEditing ? 'Editing set · live changes' : 'Student preview · read-only'}
          </p>
          <p
            className={`text-xs ${isEditing ? 'text-amber-800' : 'text-brand-700'}`}
          >
            {isEditing
              ? 'Changes apply to future assignments only — existing ones keep what students were given.'
              : "This is exactly how students see the set — answers hidden, variables filled in. You can't type or submit here."}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {canEdit && (
            <button
              type="button"
              onClick={() => setIsEditing((v) => !v)}
              data-testid="toggle-edit"
              className="rounded-md border border-ink-200 bg-white px-3 py-1.5 text-xs font-medium text-ink-700 hover:bg-ink-50"
            >
              {isEditing ? 'Done editing' : 'Edit set'}
            </button>
          )}
          <button
            type="button"
            onClick={() => navigate(-1)}
            className={`text-sm font-medium ${
              isEditing ? 'text-amber-800 hover:text-amber-900' : 'text-brand-700 hover:text-brand-900'
            }`}
          >
            ← Back
          </button>
        </div>
      </div>

      {/* AIV-3b banner reused for problem sets when editing. */}
      {isEditing && (
        <EditSafetyBanner
          assignedCount={assignedCount}
          hasGradedSubmissions={hasGraded}
          noun="this problem set"
        />
      )}

      {/* Set header */}
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">{data.title}</h1>
        <p className="mt-1 text-sm text-ink-500">
          {data.subject_name && <span>{data.subject_name}</span>}
          {data.chapter_name && <span> · {data.chapter_name}</span>}
          <span> · {data.question_count} question{data.question_count !== 1 ? 's' : ''}</span>
          {data.estimated_minutes != null && <span> · ~{data.estimated_minutes} min</span>}
        </p>
      </div>

      {/* Questions — rendered exactly as a student sees them, locked */}
      {data.questions.length === 0 ? (
        <EmptyState
          title="This set has no questions yet"
          description={
            isEditing
              ? 'Use the Add question button below to start filling it in.'
              : 'Add questions to the set, then preview again.'
          }
        />
      ) : (
        <div className="space-y-4">
          {data.questions.map((q, i) => (
            <div key={q.id} className="relative">
              <QuestionCard
                question={q}
                questionNumber={i + 1}
                answers={{}}
                onAnswerChange={() => {}}
                isSubmitted
              />
              {isEditing && (
                <div className="mt-2 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/teacher/questions/${q.id}/edit?returnTo=${encodeURIComponent(returnTo)}`,
                      )
                    }
                    className="rounded-md border border-ink-200 bg-white px-3 py-1.5 text-xs font-medium text-ink-700 hover:bg-ink-50"
                  >
                    Edit question
                  </button>
                  <button
                    type="button"
                    data-testid={`remove-${q.id}`}
                    disabled={removeQuestion.isPending}
                    onClick={() => handleRemove(q.id)}
                    className="rounded-md border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                  >
                    Remove from set
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {isEditing && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dashed border-ink-200 bg-paper px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-ink-800">Add more questions</p>
            <p className="text-xs text-ink-500">
              Pick from the question bank, or author a new question — you'll come back here when done.
            </p>
          </div>
          <Button onClick={() => navigate(addPath)} variant="brand">
            Add question
          </Button>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-100 pt-5">
        <Button
          variant="ghost"
          onClick={() => setId != null && navigate(`/teacher/problem-sets/${setId}/versions`)}
          data-testid="view-versions"
        >
          View version history
        </Button>
        <Button variant="ghost" onClick={() => navigate('/teacher')}>
          Back to dashboard
        </Button>
      </div>
    </div>
  );
};
