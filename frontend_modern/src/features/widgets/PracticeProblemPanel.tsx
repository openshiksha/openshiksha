import { useState } from 'react';
import { AIBadge, Badge, Button, Input, LoadingSpinner } from '@/shared/ui';
import { InteractiveWidget } from '@/shared/ui/InteractiveWidget';
import { usePracticeProblem, type PracticeProblemResponse } from './usePracticeProblem';

/**
 * PV-3 — the on-screen **AI practice-problem generator** for the
 * propose-and-verify practice bank.
 *
 * A plain-English topic ("mark 3/4 on a number line") → the PV-2 endpoint
 * proposes a `number-line` `{widget_config, correct_answer}`, and this
 * host-side panel renders the **verified** problem in the same live sandbox
 * preview a hand-picked widget uses, with the answer shown alongside. It is the
 * natural home for the AI a teacher wants — *a ready-made, checkable problem* —
 * sitting **outside** the network-less widget sandbox (principle 1) and
 * **outside** the grading path (principle 2): it only ever renders a preview and
 * the answer, and never reports a value to the grader.
 *
 * Iron-clad by construction:
 * - **The engine disposes, not the AI.** Every returned problem is
 *   verified-answerable server-side by PV-1 *before* it reaches this panel (an
 *   off-grid answer is deterministically snapped onto the widget's grid and
 *   re-verified), so the UI can trust the `{config, answer}` pair and drop it
 *   straight into the preview — no client-side re-checking, no parallel path.
 * - **Deterministic fallback, honest provenance.** A real proposal wears the
 *   `✨ AI-generated` badge; when the cascade falls back to the known-good safe
 *   problem (`ai_available: false`) the panel shows a neutral `Auto-problem`
 *   badge plus a friendly "AI unavailable" line. The fallback is never dressed
 *   as a real generation, and a snapped answer is flagged `Answer adjusted to
 *   the grid`.
 */

const PLACEHOLDER = 'e.g. mark 1/2 on a number line from 0 to 1';

export function PracticeProblemPanel() {
  const [topic, setTopic] = useState('mark 1/2 on a number line from 0 to 1');
  const proposal = usePracticeProblem();
  const trimmed = topic.trim();
  const canAsk = trimmed.length > 0;
  const result = proposal.data;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink-900">Generate a practice problem</h2>
        <p className="mt-1 text-sm text-ink-600">
          Describe a topic and the AI proposes a problem — but a{' '}
          <strong>deterministic engine confirms the answer is actually reachable</strong> on the
          widget before it renders. AI proposes, the engine disposes.
        </p>
      </div>

      <div className="grid gap-3">
        <Input
          label="Topic"
          value={topic}
          placeholder={PLACEHOLDER}
          spellCheck={false}
          onChange={(event) => setTopic(event.target.value)}
        />
        <div>
          <Button
            size="sm"
            disabled={!canAsk || proposal.isPending}
            onClick={() => proposal.mutate({ topic: trimmed })}
          >
            {proposal.isPending ? 'Generating…' : 'Generate & verify'}
          </Button>
        </div>
      </div>

      {proposal.isPending && (
        <div className="flex items-center gap-2 text-sm text-ink-500">
          <LoadingSpinner />
          <span>Proposing a problem and verifying it&apos;s answerable…</span>
        </div>
      )}

      {proposal.isError && (
        <p
          role="alert"
          className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          Couldn&apos;t reach the problem generator. Try again.
        </p>
      )}

      {result && <PracticeProblemResult result={result} />}
    </div>
  );
}

function formatAnswer(answer: unknown): string {
  if (answer === null || answer === undefined) return '—';
  if (typeof answer === 'number') return String(answer);
  if (typeof answer === 'boolean') return answer ? 'true' : 'false';
  if (typeof answer === 'string') return answer;
  return JSON.stringify(answer);
}

function PracticeProblemResult({ result }: { result: PracticeProblemResponse }) {
  const answer = formatAnswer(result.correct_answer?.answer);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <AIBadge modelUsed={result.model_used} stubLabel="Auto-problem" />
        {/* PV-1 guarantee, on screen: this problem was proven answerable before
            it rendered — the AI never got to decide correctness. */}
        <Badge tone="attention">✓ Verified answerable</Badge>
        {result.repaired && result.ai_available && (
          <Badge tone="neutral">Answer adjusted to the grid</Badge>
        )}
      </div>

      {/* The verified problem, in the SAME live sandbox preview a hand-picked
          widget uses. The config is verified-reachable by construction, so the
          UI just renders it — no client-side re-validation. */}
      <InteractiveWidget
        kind={result.widget_kind}
        config={result.widget_config}
        variables={{}}
        minHeight={180}
      />

      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
        <p className="text-sm font-semibold text-emerald-800">
          Answer: <span className="font-mono">{answer}</span>
        </p>
        <p className="mt-1 text-sm text-emerald-700">
          The engine confirmed a student can actually reach this value on the widget above — so the
          deterministic grader can mark it.
        </p>
      </div>

      {!result.ai_available && (
        <p className="text-xs text-ink-500">
          The AI proposer is unavailable right now — here&apos;s a known-good, verified problem
          instead.
        </p>
      )}
    </div>
  );
}
