import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Button, EmptyState, Skeleton } from '@/shared/ui';
import { QuestionCard } from './QuestionCard';
import { useMarkReviewed, useSRSDrill, type SRSReviewResult } from './useSRSDrill';

/**
 * SRS practice drill flow:
 * 1. Load chapter questions via /ai/spaced-repetition/{id}/review/
 * 2. Student answers each subpart in a familiar QuestionCard
 * 3. Submit POSTs {answers} to /mark-reviewed/ → server grades + updates SM-2
 * 4. Result screen shows score and next review date
 */
export const SRSDrillPage = () => {
  const { entryId } = useParams<{ entryId: string }>();
  const navigate = useNavigate();
  const parsedId = entryId ? parseInt(entryId, 10) : null;

  const { data: drill, isLoading, isError } = useSRSDrill(parsedId);
  const { mutate: markReviewed, isPending } = useMarkReviewed();

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<SRSReviewResult | null>(null);

  const answeredCount = useMemo(
    () => Object.values(answers).filter((v) => v && v.trim().length > 0).length,
    [answers],
  );
  const totalSubparts = useMemo(
    () => drill?.questions.reduce((sum, q) => sum + q.subparts.length, 0) ?? 0,
    [drill],
  );

  const handleAnswerChange = (subpartId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [String(subpartId)]: value }));
  };

  const handleSubmit = () => {
    if (!drill || answeredCount === 0) return;
    markReviewed(
      { entryId: drill.entry_id, answers },
      { onSuccess: (data) => setResult(data) },
    );
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-4">
        <Skeleton w="w-1/2" h="h-6" />
        <Skeleton w="w-1/3" h="h-4" />
        <div className="os-card p-6 space-y-3 mt-4">
          <Skeleton w="w-3/4" h="h-4" />
          <Skeleton w="w-full" h="h-4" />
          <Skeleton w="w-5/6" h="h-4" />
          <Skeleton w="w-full" h="h-10" rounded="rounded-lg" />
          <Skeleton w="w-full" h="h-10" rounded="rounded-lg" />
        </div>
      </div>
    );
  }

  if (isError || !drill) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <EmptyState
          title="Review session not found"
          description="This review may have been removed or is no longer available."
          action={
            <Link
              to="/student"
              className="btn-brand inline-block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
            >
              Back to dashboard
            </Link>
          }
        />
      </div>
    );
  }

  if (result) {
    const pct = Math.round(result.score * 100);
    const passed = result.score >= 0.6;
    return (
      <div className="max-w-2xl mx-auto px-4 py-10">
        <div
          className={`rounded-2xl border p-8 text-center ${
            passed ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'
          }`}
        >
          <div className="text-5xl mb-4" aria-hidden>
            {passed ? '🎉' : '📚'}
          </div>
          <h2 className="text-2xl font-display font-semibold text-ink-900 mb-2">
            {passed ? 'Great review!' : 'Keep practicing!'}
          </h2>
          <p className="text-ink-700 mb-1">
            You scored <span className="font-semibold">{pct}%</span> on{' '}
            <span className="font-semibold">{drill.chapter_name}</span>
          </p>
          <p className="text-sm text-ink-500 mb-6">
            {passed
              ? `Next review scheduled for ${result.next_review_date}`
              : 'Interval reset — see this chapter again tomorrow'}
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            <Button onClick={() => navigate('/student')}>Back to Dashboard</Button>
            <Button
              variant="ghost"
              onClick={() => {
                setAnswers({});
                setResult(null);
              }}
            >
              Review again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 sm:py-8">
      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate('/student')}
          className="text-sm text-brand-700 font-medium hover:underline mb-3 inline-flex items-center gap-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        >
          ← Back
        </button>
        <div className="flex items-center gap-3">
          <span
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-100 text-2xl"
            aria-hidden
          >
            🔁
          </span>
          <div className="min-w-0">
            <h1 className="text-xl font-display font-semibold text-ink-900 truncate">
              {drill.chapter_name}
            </h1>
            <p className="text-sm text-ink-500 truncate">
              {drill.subject_name} · Spaced review
            </p>
          </div>
        </div>
      </div>

      {drill.questions.length === 0 ? (
        <EmptyState
          title="No review questions yet"
          description={`Your teacher hasn't added questions for ${drill.chapter_name} yet.`}
          action={
            <Link
              to="/student"
              className="btn-brand inline-block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
            >
              Back to dashboard
            </Link>
          }
        />
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between text-xs text-ink-500">
            <span>
              {answeredCount} / {totalSubparts} answered
            </span>
            <span>
              {drill.questions.length} question{drill.questions.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="space-y-4">
            {drill.questions.map((question, idx) => (
              <QuestionCard
                key={question.id}
                question={question}
                questionNumber={idx + 1}
                answers={answers}
                onAnswerChange={handleAnswerChange}
                isSubmitted={false}
              />
            ))}
          </div>

          <div className="mt-6 sticky bottom-4">
            <Button
              size="lg"
              className="w-full shadow-sm"
              onClick={handleSubmit}
              disabled={isPending || answeredCount === 0}
            >
              {isPending ? 'Submitting…' : 'Submit Review'}
            </Button>
            {answeredCount === 0 && (
              <p className="text-xs text-center text-ink-400 mt-2">
                Answer at least one question to submit
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
};
