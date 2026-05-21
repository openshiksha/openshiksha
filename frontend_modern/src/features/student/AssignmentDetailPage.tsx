import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAssignmentDetail } from './useAssignmentDetail';
import { useSubmission, useCreateSubmission, usePatchSubmission } from './useSubmission';
import { QuestionCard } from './QuestionCard';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { Question } from '@/types/index';

function countSubparts(questions: Question[]): number {
  return questions.reduce((sum, q) => sum + q.subparts.length, 0);
}

function countAnswered(questions: Question[], answers: Record<string, string>): number {
  return questions.reduce(
    (sum, q) =>
      sum +
      q.subparts.filter((sp) => (answers[String(sp.id)] ?? '').trim().length > 0).length,
    0
  );
}

export const AssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const assignmentId = Number(id);
  const navigate = useNavigate();

  const { data: assignment, isLoading: assignmentLoading, error: assignmentError } =
    useAssignmentDetail(assignmentId);
  const { data: existingSubmission, isLoading: submissionLoading } =
    useSubmission(assignmentId);

  const createSubmission = useCreateSubmission();
  const patchSubmission = usePatchSubmission(assignmentId);

  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submitScore, setSubmitScore] = useState<number | null>(null);

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Once submission data loads, initialize state
  useEffect(() => {
    if (!submissionLoading) {
      if (existingSubmission) {
        setSubmissionId(existingSubmission.id);
        setAnswers(
          Object.fromEntries(
            Object.entries(existingSubmission.answers ?? {}).map(([k, v]) => [k, String(v)])
          )
        );
        if (existingSubmission.submitted_at) {
          setIsSubmitted(true);
          setSubmitScore(existingSubmission.score);
        }
      } else if (assignmentId && !createSubmission.isPending) {
        // No existing submission — create one
        createSubmission.mutate(assignmentId, {
          onSuccess: (sub) => setSubmissionId(sub.id),
        });
      }
    }
    // Only run when submission load state changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [submissionLoading, existingSubmission]);

  const questions = useMemo(
    () => assignment?.problem_set?.questions ?? [],
    [assignment]
  );
  const total = countSubparts(questions);
  const answered = countAnswered(questions, answers);

  const handleAnswerChange = useCallback(
    (subpartId: number, value: string) => {
      if (isSubmitted) return;

      setAnswers((prev) => {
        const updated = { ...prev, [String(subpartId)]: value };

        // Debounced auto-save
        if (debounceTimer.current) clearTimeout(debounceTimer.current);
        debounceTimer.current = setTimeout(() => {
          if (submissionId) {
            const answeredCount = countAnswered(questions, updated);
            patchSubmission.mutate({
              id: submissionId,
              data: {
                answers: updated,
                completion: total > 0 ? answeredCount / total : 0,
              },
            });
          }
        }, 2000);

        return updated;
      });
    },
    [isSubmitted, submissionId, questions, total, patchSubmission]
  );

  const handleSubmit = () => {
    if (!submissionId) return;
    patchSubmission.mutate(
      {
        id: submissionId,
        data: {
          answers,
          completion: total > 0 ? answered / total : 0,
          submitted_at: new Date().toISOString(),
        },
      },
      {
        onSuccess: (sub) => {
          setIsSubmitted(true);
          setSubmitScore(sub.score);
          setShowConfirm(false);
        },
      }
    );
  };

  if (assignmentLoading || submissionLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (assignmentError || !assignment) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Assignment not found or could not be loaded.</p>
        <button
          onClick={() => navigate('/student')}
          className="mt-4 text-sm text-indigo-600 hover:underline"
        >
          Back to dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/student')}
          className="text-sm text-indigo-600 hover:underline mb-3 flex items-center gap-1"
        >
          <span>&#8592;</span> Back to assignments
        </button>
        <p className="text-xs font-medium text-indigo-600 uppercase tracking-wide">
          {assignment.problem_set.subject.name}
        </p>
        <h1 className="text-xl font-bold text-gray-900 mt-0.5">
          {assignment.problem_set.title}
        </h1>
        <p className="text-sm text-gray-500">{assignment.problem_set.chapter.name}</p>
      </div>

      {/* Progress bar */}
      {!isSubmitted && total > 0 && (
        <div className="mb-6">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>{answered} of {total} answered</span>
            <span>{Math.round((answered / total) * 100)}%</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all duration-300"
              style={{ width: `${(answered / total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Submitted state */}
      {isSubmitted && (
        <div className={`mb-6 rounded-xl p-4 text-center ${
          submitScore !== null
            ? submitScore >= 0.8
              ? 'bg-green-50 border border-green-200'
              : submitScore >= 0.5
              ? 'bg-yellow-50 border border-yellow-200'
              : 'bg-red-50 border border-red-200'
            : 'bg-indigo-50 border border-indigo-200'
        }`}>
          {submitScore !== null ? (
            <>
              <p className="text-lg font-bold text-gray-900">
                {Math.round(submitScore * 100)}%
              </p>
              <p className="text-sm text-gray-600 mt-0.5">Assignment submitted</p>
            </>
          ) : (
            <>
              <p className="font-semibold text-indigo-800">Submitted</p>
              <p className="text-sm text-indigo-600 mt-0.5">Grading in progress...</p>
            </>
          )}
        </div>
      )}

      {/* Questions */}
      {questions.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>No questions in this assignment.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((question: Question, idx: number) => (
            <QuestionCard
              key={question.id}
              question={question}
              questionNumber={idx + 1}
              answers={answers}
              onAnswerChange={handleAnswerChange}
              isSubmitted={isSubmitted}
            />
          ))}
        </div>
      )}

      {/* Submit button */}
      {!isSubmitted && questions.length > 0 && (
        <div className="mt-8 flex justify-end">
          <button
            onClick={() => setShowConfirm(true)}
            disabled={answered === 0}
            className="w-full sm:w-auto bg-indigo-600 text-white px-6 py-3 sm:py-2.5 rounded-lg font-medium text-sm hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Submit assignment
          </button>
        </div>
      )}

      {/* Confirm dialog */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Submit assignment?</h3>
            <p className="text-sm text-gray-500 mt-1">
              You have answered {answered} of {total} questions. You cannot change your answers after submitting.
            </p>
            <div className="flex gap-3 mt-5 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={patchSubmission.isPending}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {patchSubmission.isPending ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
