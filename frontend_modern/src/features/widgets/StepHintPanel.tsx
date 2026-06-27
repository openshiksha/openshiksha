import { useEffect } from 'react';
import { AIBadge, Badge, Button, LoadingSpinner } from '@/shared/ui';
import { useStepHint } from './useStepHint';

/**
 * GSV-4 — the on-screen **AI wrong-step coach** for the guided step-validator.
 *
 * Given two successive lines of a student's working (`previous` → `current`),
 * this host-side panel asks the GSV-3 endpoint *why* the step is wrong and
 * renders a short, grounded explanation. It is the natural home for the AI a
 * struggling student needs — *what went wrong* — sitting **outside** the
 * network-less widget sandbox (principle 1) and **outside** the grading path
 * (principle 2): it only ever renders explanatory text and never reports a
 * value to the grader.
 *
 * Iron-clad by construction:
 * - **AI never grades.** The `verdict` is always the deterministic engine's
 *   call (the backend re-runs `check_step` and only calls the LLM on a step it
 *   has *already* ruled wrong). A `correct` step shows a green note and the LLM
 *   is never invoked; an `unparseable` line shows the engine's neutral reason.
 * - **Deterministic fallback, honest provenance.** A real explanation wears the
 *   `✨ AI-generated` badge; when the cascade falls back to the static hint
 *   (`ai_available: false`) the panel shows a neutral `Auto-explanation` badge
 *   plus a friendly "AI unavailable" line. The stub is never dressed as real.
 *
 * `GSV-4b` will feed `previous`/`current` automatically from the `step-solver`
 * widget's wrong-step events; today the playground supplies them so the coach
 * is demoable and tested end to end against the live endpoint.
 */
interface StepHintPanelProps {
  /** The line the student had correct so far. */
  previous: string;
  /** The new (suspected-wrong) line the student wrote. */
  current: string;
}

export function StepHintPanel({ previous, current }: StepHintPanelProps) {
  const stepHint = useStepHint();
  const { reset } = stepHint;

  const trimmedPrev = previous.trim();
  const trimmedCur = current.trim();
  const canAsk = trimmedPrev.length > 0 && trimmedCur.length > 0;

  // The two lines define the question; if either changes, the previous answer
  // is stale, so clear it. (The student must explicitly ask again.)
  useEffect(() => {
    reset();
  }, [trimmedPrev, trimmedCur, reset]);

  const result = stepHint.data;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-widest text-ink-400">
          AI step coach
        </p>
        <Button
          size="sm"
          variant="ghost"
          disabled={!canAsk || stepHint.isPending}
          onClick={() => stepHint.mutate({ previous: trimmedPrev, current: trimmedCur })}
        >
          {stepHint.isPending ? 'Checking…' : 'Why is this wrong?'}
        </Button>
      </div>

      {!canAsk && (
        <p className="text-sm text-ink-500">
          Enter a previous line and the new line to get a grounded explanation.
        </p>
      )}

      {stepHint.isPending && (
        <div className="flex items-center gap-2 text-sm text-ink-500">
          <LoadingSpinner />
          <span>Asking the coach…</span>
        </div>
      )}

      {stepHint.isError && (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          Couldn&apos;t reach the step coach. Try again.
        </p>
      )}

      {result && <StepHintResult result={result} />}
    </div>
  );
}

function StepHintResult({ result }: { result: NonNullable<ReturnType<typeof useStepHint>['data']> }) {
  // The verdict is ALWAYS the deterministic engine's — never the LLM's.
  if (result.verdict === 'correct') {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
        <p className="flex items-center gap-2 text-sm font-semibold text-emerald-800">
          <span aria-hidden="true">✓</span> This step looks right.
        </p>
        <p className="mt-1 text-sm text-emerald-700">{result.reason}</p>
      </div>
    );
  }

  if (result.verdict === 'unparseable') {
    return (
      <div className="rounded-lg border border-ink-200 bg-ink-50 px-4 py-3">
        <p className="text-sm font-semibold text-ink-700">Couldn&apos;t check this line.</p>
        <p className="mt-1 text-sm text-ink-600">{result.reason}</p>
      </div>
    );
  }

  // verdict === 'wrong' — the only branch the LLM ever runs on.
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="urgent">✗ This changes the answer</Badge>
        <AIBadge modelUsed={result.model_used ?? 'stub'} stubLabel="Auto-explanation" />
      </div>
      <p className="mt-2 text-sm text-ink-700">{result.reason}</p>
      {result.hint && (
        <p className="mt-2 text-sm font-medium text-ink-900">{result.hint}</p>
      )}
      {!result.ai_available && (
        <p className="mt-2 text-xs text-ink-500">
          The AI coach is unavailable right now — here&apos;s a safe pointer to re-check the step.
        </p>
      )}
    </div>
  );
}
