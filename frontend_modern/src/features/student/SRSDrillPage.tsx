import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
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
    [answers]
  );
  const totalSubparts = useMemo(
    () => drill?.questions.reduce((sum, q) => sum + q.subparts.length, 0) ?? 0,
    [drill]
  );

  const handleAnswerChange = (subpartId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [String(subpartId)]: value }));
  };

  const handleSubmit = () => {
    if (!drill || answeredCount === 0) return;
    markReviewed(
      { entryId: drill.entry_id, answers },
      { onSuccess: (data) => setResult(data) }
    );
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-gray-500">
          <div className="h-10 w-10 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin" />
          <p className="text-sm">Loading your review session…</p>
        </div>
      </div>
    );
  }

  if (isError || !drill) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <div className="rounded-xl border border-gray-200 bg-white p-8">
          <p className="text-base font-semibold text-gray-900 mb-2">
            Review session not found
          </p>
          <p className="text-sm text-gray-500 mb-4">
            This review may have been removed or is no longer available.
          </p>
          <Link
            to="/student"
            className="inline-block bg-indigo-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Back to dashboard
          </Link>
        </div>
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
            passed
              ? 'border-green-200 bg-green-50'
              : 'border-amber-200 bg-amber-50'
          }`}
        >
          <div className="text-5xl mb-4" aria-hidden>
            {passed ? '🎉' : '📚'}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {passed ? 'Great review!' : 'Keep practicing!'}
          </h2>
          <p className="text-gray-700 mb-1">
            You scored <span className="font-semibold">{pct}%</span> on{' '}
            <span className="font-semibold">{drill.chapter_name}</span>
          </p>
          <p className="text-sm text-gray-500 mb-6">
            {passed
              ? `Next review scheduled for ${result.next_review_date}`
              : 'Interval reset — see this chapter again tomorrow'}
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            <button
              type="button"
              onClick={() => navigate('/student')}
              className="bg-indigo-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Back to Dashboard
            </button>
            <button
              type="button"
              onClick={() => {
                setAnswers({});
                setResult(null);
              }}
              className="bg-white border border-gray-300 text-gray-700 px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Review again
            </button>
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
          className="text-sm text-indigo-600 hover:text-indigo-800 mb-3 inline-flex items-center gap-1 transition-colors"
        >
          ← Back
        </button>
        <div className="flex items-center gap-3">
          <span
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-orange-100 text-2xl"
            aria-hidden
          >
            🔁
          </span>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-gray-900 truncate">
              {drill.chapter_name}
            </h1>
            <p className="text-sm text-gray-500 truncate">
              {drill.subject_name} · Spaced review
            </p>
          </div>
        </div>
      </div>

      {drill.questions.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
          <div className="text-4xl mb-3" aria-hidden>
            📭
          </div>
          <p className="text-base font-semibold text-gray-900 mb-1">
            No review questions yet
          </p>
          <p className="text-sm text-gray-500 mb-5">
            Your teacher hasn't added questions for {drill.chapter_name} yet.
          </p>
          <Link
            to="/student"
            className="inline-block bg-indigo-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Back to dashboard
          </Link>
        </div>
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between text-xs text-gray-500">
            <span>
              {answeredCount} / {totalSubparts} answered
            </span>
            <span>{drill.questions.length} question{drill.questions.length !== 1 ? 's' : ''}</span>
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
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isPending || answeredCount === 0}
              className="w-full bg-indigo-600 text-white px-8 py-3 rounded-xl font-semibold shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isPending ? 'Submitting…' : 'Submit Review'}
            </button>
            {answeredCount === 0 && (
              <p className="text-xs text-center text-gray-400 mt-2">
                Answer at least one question to submit
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
};
