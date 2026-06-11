import { useEffect, useState } from 'react';
import { RichContent } from '@/shared/ui/RichContent';
import { AIBadge, Skeleton, isAIStub } from '@/shared/ui';
import { useExplanationList, useGenerateExplanation } from './useExplanation';

interface ExplanationPanelProps {
  subpartId: number;
  studentAnswer: string;
  isCorrect: boolean;
  /** Poll cadence while the async generation task runs. Overridable for tests. */
  pollIntervalMs?: number;
  /** Polls before giving up (~30 s at the default cadence). */
  maxPollAttempts?: number;
}

/**
 * Post-submit "Explain this answer" affordance — the first consumer of the
 * /ai/explanations/ endpoints. Generation is async (202 + Celery), so after
 * triggering it the panel polls the student-scoped list until the explanation
 * row appears, then renders it with the standard AI-provenance badge.
 *
 * Explanations persist server-side: if one already exists for the subpart the
 * panel shows it directly and never re-generates.
 */
export const ExplanationPanel = ({
  subpartId,
  studentAnswer,
  isCorrect,
  pollIntervalMs = 2000,
  maxPollAttempts = 15,
}: ExplanationPanelProps) => {
  const [requested, setRequested] = useState(false);
  const [attempts, setAttempts] = useState(0);

  const listQuery = useExplanationList(subpartId, requested);
  const generate = useGenerateExplanation();

  const explanation = listQuery.data?.[0];
  const timedOut = attempts >= maxPollAttempts;

  // First list fetch came back empty → kick off generation exactly once
  // (generate.isIdle guards re-fires; reset() re-arms it for retry).
  useEffect(() => {
    if (requested && listQuery.isSuccess && !explanation && generate.isIdle && !timedOut) {
      generate.mutate({
        subpart_id: subpartId,
        student_answer: studentAnswer,
        is_correct: isCorrect,
      });
    }
  }, [requested, listQuery.isSuccess, explanation, generate, timedOut, subpartId, studentAnswer, isCorrect]);

  // Poll the list while the Celery task runs; give up after maxPollAttempts.
  useEffect(() => {
    if (!requested || explanation || !generate.isSuccess || timedOut) return;
    const timer = setTimeout(() => {
      setAttempts((n) => n + 1);
      void listQuery.refetch();
    }, pollIntervalMs);
    return () => clearTimeout(timer);
  }, [requested, explanation, generate.isSuccess, timedOut, attempts, pollIntervalMs, listQuery]);

  if (!requested) {
    return (
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setRequested(true)}
          className="text-xs font-medium text-brand-700 hover:text-brand-800 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline"
        >
          ✨ Explain this answer
        </button>
      </div>
    );
  }

  if (explanation) {
    const isStub = isAIStub(explanation.model_used);
    return (
      <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50 p-3">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-medium text-brand-800">
            {isCorrect ? 'Why this answer is right' : 'Where this went wrong'}
          </span>
          <AIBadge modelUsed={explanation.model_used} stubLabel="Auto-explanation" />
        </div>
        <div className="text-sm text-ink-800 leading-relaxed">
          <RichContent text={explanation.explanation_text} variant="block" />
        </div>
        {isStub && (
          <p className="mt-1.5 text-[10px] text-ink-400">
            Generated without an AI model — explanations get richer once AI is configured.
          </p>
        )}
      </div>
    );
  }

  if (generate.isError || listQuery.isError || timedOut) {
    return (
      <div className="mt-3 text-xs text-rose-600">
        Couldn&apos;t fetch an explanation just now. Please try again in a moment.{' '}
        <button
          type="button"
          onClick={() => {
            setAttempts(0);
            generate.reset();
            void listQuery.refetch();
          }}
          className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50 p-3">
      <p className="text-xs text-brand-800 mb-2">Writing your explanation…</p>
      <div className="space-y-1.5">
        <Skeleton w="w-full" h="h-3" />
        <Skeleton w="w-5/6" h="h-3" />
        <Skeleton w="w-2/3" h="h-3" />
      </div>
    </div>
  );
};
