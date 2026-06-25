import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAssignmentDetail } from './useAssignmentDetail';
import { useSubmission, useCreateSubmission, usePatchSubmission } from './useSubmission';
import { QuestionCard } from './QuestionCard';
import { VideosPanel } from './VideosPanel';
import { SyncStatus } from './SyncStatus';
import { Button, EmptyState, LoadingSpinner } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { useOnlineStatus } from '@/shared/hooks/useOnlineStatus';
import type { Question } from '@/types/index';

function countSubparts(questions: Question[]): number {
  return questions.reduce((sum, q) => sum + q.subparts.length, 0);
}

function countAnswered(questions: Question[], answers: Record<string, string>): number {
  return questions.reduce(
    (sum, q) =>
      sum + q.subparts.filter((sp) => (answers[String(sp.id)] ?? '').trim().length > 0).length,
    0,
  );
}

export const AssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const assignmentId = Number(id);
  const navigate = useNavigate();
  const t = useT();

  const { data: assignment, isLoading: assignmentLoading, error: assignmentError } =
    useAssignmentDetail(assignmentId);
  const { data: existingSubmission, isLoading: submissionLoading } = useSubmission(assignmentId);

  const createSubmission = useCreateSubmission();
  const patchSubmission = usePatchSubmission(assignmentId);
  const online = useOnlineStatus();

  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [submitScore, setSubmitScore] = useState<number | null>(null);
  // MSO-9: the student hit submit while offline — the submit mutation is queued
  // (MSO-7) and will replay/grade on reconnect. Until the server confirms, show a
  // "submitted — will be graded when back online" card instead of a fake score.
  const [submittedOffline, setSubmittedOffline] = useState(false);

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initialize local state from a loaded submission (during render — react.dev/learn/you-might-not-need-an-effect)
  const [syncedSubmission, setSyncedSubmission] = useState<typeof existingSubmission | undefined>(
    undefined,
  );
  if (!submissionLoading && existingSubmission && existingSubmission !== syncedSubmission) {
    setSyncedSubmission(existingSubmission);
    setSubmissionId(existingSubmission.id);
    setAnswers(
      Object.fromEntries(
        Object.entries(existingSubmission.answers ?? {}).map(([k, v]) => [k, String(v)]),
      ),
    );
    if (existingSubmission.submitted_at) {
      setIsSubmitted(true);
      setSubmitScore(existingSubmission.score);
    }
  }

  // No submission once loading settles — create one (network side effect stays in an effect)
  useEffect(() => {
    if (!submissionLoading && !existingSubmission && assignmentId && !createSubmission.isPending) {
      createSubmission.mutate(assignmentId, {
        onSuccess: (sub) => setSubmissionId(sub.id),
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [submissionLoading, existingSubmission]);

  const questions = useMemo(() => assignment?.problem_set?.questions ?? [], [assignment]);
  const total = countSubparts(questions);
  const answered = countAnswered(questions, answers);

  const handleAnswerChange = useCallback(
    (subpartId: number, value: string) => {
      if (isSubmitted) return;

      setAnswers((prev) => {
        const updated = { ...prev, [String(subpartId)]: value };

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
    [isSubmitted, submissionId, questions, total, patchSubmission],
  );

  const handleSubmit = () => {
    if (!submissionId) return;
    // Optimistically lock into a submitted view immediately. Online this resolves
    // to the score (or the async "grading…" state) on success; offline the
    // mutation pauses (MSO-7) and we show the "will be graded when back online"
    // card until it replays onto the idempotent server (MSO-6).
    setIsSubmitted(true);
    setShowConfirm(false);
    if (!online) setSubmittedOffline(true);
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
          // Server confirmed (immediately online, or after the queued replay):
          // reconcile the real score and drop the offline-pending state.
          setSubmitScore(sub.score);
          setSubmittedOffline(false);
        },
        onError: () => {
          // The replay ultimately failed (e.g. the assignment closed while the
          // student was offline). Re-open the form so they aren't stuck — the
          // global sync indicator (MSO-8) already shows the failure.
          setIsSubmitted(false);
          setSubmittedOffline(false);
        },
      },
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
      <div className="max-w-2xl mx-auto px-4 py-16">
        <EmptyState
          title={t('assignmentDetail.notFoundTitle')}
          description={t('assignmentDetail.notFoundDescription')}
          action={
            <Button variant="ghost" size="sm" onClick={() => navigate('/student')}>
              {t('assignmentDetail.backToDashboard')}
            </Button>
          }
        />
      </div>
    );
  }

  // Unlock motif on the post-submit score card.
  const scoreBg =
    submitScore !== null
      ? submitScore >= 0.8
        ? 'bg-emerald-50 border-emerald-200'
        : submitScore >= 0.5
          ? 'bg-amber-50 border-amber-200'
          : 'bg-rose-50 border-rose-200'
      : 'bg-brand-50 border-brand-200';

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate('/student')}
          className="text-sm text-brand-700 font-medium hover:underline mb-3 flex items-center gap-1 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        >
          <span>&#8592;</span> {t('assignmentDetail.back')}
        </button>
        <p className="text-xs font-semibold text-brand-700 uppercase tracking-wide">
          {assignment.problem_set.subject.name}
        </p>
        <h1 className="text-xl font-display font-semibold text-ink-900 mt-0.5">
          {assignment.problem_set.title}
        </h1>
        <p className="text-sm text-ink-500">{assignment.problem_set.chapter.name}</p>
        <div className="mt-2">
          <SyncStatus />
        </div>
      </div>

      {!isSubmitted && total > 0 && (
        <div className="mb-6">
          <div className="flex justify-between text-xs text-ink-500 mb-1">
            <span>{t('assignmentDetail.answeredCount', { answered, total })}</span>
            <span>{Math.round((answered / total) * 100)}%</span>
          </div>
          <div className="h-1.5 bg-ink-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all duration-300 motion-reduce:transition-none"
              style={{ width: `${(answered / total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {isSubmitted && (
        // A11Y-17: announce the post-submit outcome (score / "grading…" /
        // "submitted offline") to screen-reader users — the card appears
        // dynamically after submit, so without a polite live region the result
        // is silent. `aria-live="polite"` waits for the SR to finish the user's
        // current utterance before reading the score (WCAG 4.1.3 Status Messages).
        <div
          role="status"
          aria-live="polite"
          className={`mb-6 rounded-xl p-4 text-center border ${scoreBg}`}
        >
          {submittedOffline ? (
            <>
              <p className="font-display font-semibold text-brand-800">
                {t('assignmentDetail.submittedOfflineTitle')}
              </p>
              <p className="text-sm text-brand-700 mt-0.5">
                {t('assignmentDetail.gradePending')}
              </p>
            </>
          ) : submitScore !== null ? (
            <>
              <p className="text-2xl font-display font-semibold text-ink-900">
                {Math.round(submitScore * 100)}%
              </p>
              <p className="text-sm text-ink-700 mt-0.5">{t('assignmentDetail.submittedNice')}</p>
            </>
          ) : (
            <>
              <p className="font-display font-semibold text-brand-800">
                {t('assignmentDetail.submittedTitle')}
              </p>
              <p className="text-sm text-brand-700 mt-0.5">{t('assignmentDetail.grading')}</p>
            </>
          )}
        </div>
      )}

      {questions.length === 0 ? (
        <EmptyState title={t('assignmentDetail.noQuestions')} />
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
              explanationScore={submitScore}
            />
          ))}
        </div>
      )}

      {assignment.problem_set.chapter?.id && (
        <VideosPanel chapterId={assignment.problem_set.chapter.id} />
      )}

      {!isSubmitted && questions.length > 0 && (
        <div className="mt-8 flex justify-end">
          <Button
            size="lg"
            className="w-full sm:w-auto"
            onClick={() => setShowConfirm(true)}
            disabled={answered === 0}
          >
            {t('assignmentDetail.submit')}
          </Button>
        </div>
      )}

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4">
          <div className="os-card p-6 max-w-sm w-full shadow-xl">
            <h3 className="text-lg font-display font-semibold text-ink-900">
              {t('assignmentDetail.confirmTitle')}
            </h3>
            <p className="text-sm text-ink-500 mt-1">
              {t('assignmentDetail.confirmBody', { answered, total })}
            </p>
            <div className="flex gap-3 mt-5 justify-end">
              <Button variant="ghost" size="sm" onClick={() => setShowConfirm(false)}>
                {t('common.cancel')}
              </Button>
              <Button size="sm" onClick={handleSubmit} disabled={patchSubmission.isPending}>
                {patchSubmission.isPending
                  ? t('assignmentDetail.submitting')
                  : t('assignmentDetail.confirmSubmit')}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
