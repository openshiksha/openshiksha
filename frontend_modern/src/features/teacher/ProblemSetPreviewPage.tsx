import { useNavigate, useParams } from 'react-router-dom';
import { useProblemSetPreview } from './useProblemSetPreview';
import { QuestionCard } from '../student/QuestionCard';
import { Button, EmptyState, LoadingSpinner } from '@/shared/ui';

/**
 * Read-only "view as student" preview of a problem set.
 *
 * Renders each question through the **same `<QuestionCard>` students use** on
 * the assignment page — correct answers stripped, `{{var}}` substituted, MCQs
 * shuffled (the backend's student serializer does all of that). Inputs are
 * locked via `isSubmitted` so nothing can be typed or submitted: a teacher is
 * inspecting, not solving.
 */
export const ProblemSetPreviewPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const setId = id ? Number(id) : null;
  const { data, isLoading, isError } = useProblemSetPreview(setId);

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

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      {/* Read-only student-preview banner */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3">
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
          <svg viewBox="0 0 20 20" className="h-4 w-4" fill="currentColor">
            <path d="M10 4C5.5 4 2 7.5 1 10c1 2.5 4.5 6 9 6s8-3.5 9-6c-1-2.5-4.5-6-9-6zm0 9a3 3 0 110-6 3 3 0 010 6z" />
          </svg>
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-brand-900">Student preview · read-only</p>
          <p className="text-xs text-brand-700">
            This is exactly how students see the set — answers hidden, variables filled in. You
            can't type or submit here.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-sm font-medium text-brand-700 hover:text-brand-900"
        >
          ← Back
        </button>
      </div>

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
          description="Add questions to the set, then preview again."
        />
      ) : (
        <div className="space-y-4">
          {data.questions.map((q, i) => (
            <QuestionCard
              key={q.id}
              question={q}
              questionNumber={i + 1}
              answers={{}}
              onAnswerChange={() => {}}
              isSubmitted
            />
          ))}
        </div>
      )}

      <div className="flex justify-end border-t border-ink-100 pt-5">
        <Button variant="ghost" onClick={() => navigate('/teacher')}>
          Back to dashboard
        </Button>
      </div>
    </div>
  );
};
