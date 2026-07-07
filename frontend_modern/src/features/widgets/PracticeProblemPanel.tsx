import { useState } from 'react';
import { AIBadge, Badge, Button, Input, LoadingSpinner } from '@/shared/ui';
import { InteractiveWidget } from '@/shared/ui/InteractiveWidget';
import {
  usePracticeProblem,
  type PracticeProblemResponse,
  type PracticeVariableConstraint,
} from './usePracticeProblem';

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
 * - **Per-student randomization, verified for all (PV-5b).** An "each student
 *   gets a different value" toggle sets `allow_variables`; a randomized answer
 *   only ever arrives after PV-1 sampled its ranges over synthetic students and
 *   proved every draw reachable, and it wears a `🎲 Randomized per student`
 *   pill with the validated ranges shown.
 */

const PLACEHOLDER = 'e.g. mark 1/2 on a number line from 0 to 1';

export function PracticeProblemPanel() {
  const [topic, setTopic] = useState('mark 1/2 on a number line from 0 to 1');
  // PV-5b — the "each student gets a different value" toggle sets
  // `allow_variables` on the PV-2 call. The AI may then propose the answer as
  // a croupier {{var}} expression; PV-1's reachable-for-all sampling gates it
  // server-side, so a randomized problem is verified for *every* student
  // before it can render here.
  const [allowVariables, setAllowVariables] = useState(false);
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
        {/* PV-5b: opt in to per-student randomisation. The answer becomes a
            {{var}} expression whose ranges the deterministic verifier samples
            for every student; the grader stays deterministic throughout. */}
        <label className="flex items-start gap-2 text-xs">
          <input
            type="checkbox"
            checked={allowVariables}
            onChange={(event) => setAllowVariables(event.target.checked)}
            className="mt-0.5 h-4 w-4 accent-brand-600"
          />
          <span>
            <span className="font-semibold text-ink-900">Each student gets a different value</span>
            <span className="block text-ink-500">
              The AI proposes a randomized answer — the engine verifies it&apos;s reachable for
              every student before it ships.
            </span>
          </span>
        </label>
        <div>
          <Button
            size="sm"
            disabled={!canAsk || proposal.isPending}
            onClick={() => proposal.mutate({ topic: trimmed, allow_variables: allowVariables })}
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

function formatRange(name: string, range: PracticeVariableConstraint): string {
  const kind = range.integer ? 'whole numbers' : 'decimals';
  return `{{${name}}}: ${range.min} to ${range.max} (${kind})`;
}

function PracticeProblemResult({ result }: { result: PracticeProblemResponse }) {
  const answer = formatAnswer(result.correct_answer?.answer);
  // PV-5b: constraints are non-empty only when PV-1 verified the randomized
  // answer reachable for every sampled student (verdict `ok_variable`); the
  // safe default and a concrete-value proposal both carry `{}`.
  const constraints = result.variable_constraints ?? {};
  const randomized = Object.keys(constraints).length > 0;

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
        {randomized && (
          <span className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-900">
            🎲 Randomized per student
          </span>
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
          {randomized
            ? 'Each student gets a different value drawn from the ranges below — the engine sampled them all and confirmed every one is reachable on the widget above, so the deterministic grader can mark each student.'
            : 'The engine confirmed a student can actually reach this value on the widget above — so the deterministic grader can mark it.'}
        </p>
        {randomized && (
          <p className="mt-1 text-sm text-violet-700">
            <span className="font-mono">
              {Object.entries(constraints)
                .map(([name, range]) => formatRange(name, range))
                .join(' · ')}
            </span>
          </p>
        )}
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
