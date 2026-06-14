import { useEffect, useState } from 'react';
import { RichContent } from '@/shared/ui/RichContent';
import { AIBadge, Skeleton, isAIStub } from '@/shared/ui';
import { useI18n, toAiLanguage, type Locale } from '@/shared/i18n';
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
 * Explanations persist server-side and generate in the reader's language
 * (LA-4). If a stored explanation's language differs from the active locale
 * it is still rendered (never block content) with a regenerate affordance —
 * the backend rewrites the same row in the requested language.
 */
export const ExplanationPanel = ({
  subpartId,
  studentAnswer,
  isCorrect,
  pollIntervalMs = 2000,
  maxPollAttempts = 15,
}: ExplanationPanelProps) => {
  const { t, locale } = useI18n();
  const [requested, setRequested] = useState(false);
  const [attempts, setAttempts] = useState(0);
  // Set while a language-change regeneration is in flight; polling continues
  // until the stored row's language matches it.
  const [regenLanguage, setRegenLanguage] = useState<Locale | null>(null);

  const listQuery = useExplanationList(subpartId, requested);
  const generate = useGenerateExplanation();

  const explanation = listQuery.data?.[0];
  const timedOut = attempts >= maxPollAttempts;
  const awaitingRegen = !!regenLanguage && explanation?.language !== regenLanguage;

  // First list fetch came back empty → kick off generation exactly once
  // (generate.isIdle guards re-fires; reset() re-arms it for retry).
  useEffect(() => {
    if (requested && listQuery.isSuccess && !explanation && generate.isIdle && !timedOut) {
      generate.mutate({
        subpart_id: subpartId,
        student_answer: studentAnswer,
        is_correct: isCorrect,
        language: toAiLanguage(locale),
      });
    }
  }, [requested, listQuery.isSuccess, explanation, generate, timedOut, subpartId, studentAnswer, isCorrect, locale]);

  // Poll the list while the Celery task runs (initial generation or a
  // language regeneration); give up after maxPollAttempts.
  useEffect(() => {
    if (!requested || !generate.isSuccess || timedOut) return;
    if (explanation && !awaitingRegen) return;
    const timer = setTimeout(() => {
      setAttempts((n) => n + 1);
      void listQuery.refetch();
    }, pollIntervalMs);
    return () => clearTimeout(timer);
  }, [requested, explanation, awaitingRegen, generate.isSuccess, timedOut, attempts, pollIntervalMs, listQuery]);

  const handleRegenerate = () => {
    setAttempts(0);
    // Store the *AI* language (mr → en) so the regen-complete check below
    // matches the language the backend actually generates in.
    setRegenLanguage(toAiLanguage(locale));
    generate.mutate({
      subpart_id: subpartId,
      student_answer: studentAnswer,
      is_correct: isCorrect,
      language: toAiLanguage(locale),
    });
  };

  if (!requested) {
    return (
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setRequested(true)}
          className="text-xs font-medium text-brand-700 hover:text-brand-800 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline"
        >
          {t('explanation.cta')}
        </button>
      </div>
    );
  }

  if (explanation) {
    const isStub = isAIStub(explanation.model_used);
    const languageMismatch = explanation.language !== locale;
    const regenerating = (awaitingRegen || generate.isPending) && !timedOut;
    return (
      <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50 p-3">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-medium text-brand-800">
            {isCorrect ? t('explanation.whyRight') : t('explanation.whereWrong')}
          </span>
          <AIBadge modelUsed={explanation.model_used} stubLabel="Auto-explanation" />
        </div>
        <div className="text-sm text-ink-800 leading-relaxed" lang={explanation.language}>
          <RichContent text={explanation.explanation_text} variant="block" />
        </div>
        {isStub && (
          <p className="mt-1.5 text-[10px] text-ink-400">{t('explanation.stubNote')}</p>
        )}
        {languageMismatch &&
          (regenerating ? (
            <p className="mt-2 text-xs text-brand-700">{t('explanation.regenerating')}</p>
          ) : (
            <button
              type="button"
              onClick={handleRegenerate}
              className="mt-2 text-xs font-medium text-brand-700 hover:text-brand-800 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline"
            >
              {t('explanation.regenerateInLocale')}
            </button>
          ))}
      </div>
    );
  }

  if (generate.isError || listQuery.isError || timedOut) {
    return (
      <div className="mt-3 text-xs text-rose-600">
        {t('explanation.error')}{' '}
        <button
          type="button"
          onClick={() => {
            setAttempts(0);
            generate.reset();
            void listQuery.refetch();
          }}
          className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
        >
          {t('explanation.retry')}
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50 p-3">
      <p className="text-xs text-brand-800 mb-2">{t('explanation.writing')}</p>
      <div className="space-y-1.5">
        <Skeleton w="w-full" h="h-3" />
        <Skeleton w="w-5/6" h="h-3" />
        <Skeleton w="w-2/3" h="h-3" />
      </div>
    </div>
  );
};
