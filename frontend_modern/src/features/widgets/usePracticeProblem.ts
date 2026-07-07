import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

/**
 * PV-3 — Propose-and-verify practice bank: the **AI problem-proposer** call.
 *
 * Sends a plain-English topic to the teacher-only PV-2 endpoint
 * `POST /ai/practice-problem/`, which returns a `number-line`
 * `{widget_config, correct_answer}` practice problem. The flagship safety
 * property — **the answer is provably reachable on the widget** — is enforced
 * *server-side*: PV-1's deterministic `verify_widget_problem` engine gates every
 * proposal, and an off-grid answer is deterministically snapped onto the
 * widget's own grid and re-verified before it can return. So the
 * `{widget_config, correct_answer}` this hook returns is **verified-answerable by
 * construction** (the exact DTB-4 "¾ on a 0.25 grid snaps to 0.8" bug class is
 * caught before it ever reaches the UI). **AI proposes, the engine disposes** —
 * correctness is never AI-decided.
 *
 * Provenance is honest:
 * - `ai_available: true`  → a real LLM proposed the problem (possibly
 *   `repaired: true` when its answer was snapped onto the grid); surface the
 *   `✨ AI-generated` badge.
 * - `ai_available: false` → the cascade was exhausted / the proposal was
 *   unsalvageable and the backend returned its known-good, PV-1-passed
 *   `safe_default` problem; `model_used` is `'stub'`/`'safe_default'` and the UI
 *   shows a neutral `Auto-…` badge plus a friendly "AI unavailable" line.
 *
 * This is a *host* surface (principle 1): the widget runtime is a network-less
 * sandbox, so the proposer lives outside the iframe and consumes this endpoint.
 * The `correct_answer` rides back in the grader's own `{"answer": <value>}`
 * shape and is guaranteed markable — the grader itself is untouched (principle 2).
 */

/**
 * One per-student sampling range for a `{{var}}` token in a randomized
 * `correct_answer` (PV-5). Mirrors the backend's validated constraint shape
 * (`{min, max, integer[, decimals]}`). These are validated server-side and the
 * expression is PV-1-verified reachable for every sampled student, so the UI
 * can trust and display them verbatim.
 */
export interface PracticeVariableConstraint {
  min: number;
  max: number;
  integer: boolean;
  decimals?: number;
}

export interface PracticeProblemRequest {
  /** What the problem should be about ("mark 3/4 on a number line"). */
  topic: string;
  /**
   * PV-5b — opt in to per-student randomisation. When `true`, the AI may make
   * `correct_answer` a croupier `{{var}}` expression; PV-1 then proves it
   * reachable for *every* sampled student before the problem can return, and
   * the response carries the validated `variable_constraints`.
   */
  allow_variables?: boolean;
}

export interface PracticeProblemResponse {
  /** Always `number-line` today (the answer-producing kind where reachability binds). */
  widget_kind: string;
  /** The verified, schema-valid widget config. */
  widget_config: Record<string, unknown>;
  /**
   * The correct answer in the grader's own shape — `{"answer": <value>}` —
   * guaranteed reachable on `widget_config`.
   */
  correct_answer: { answer: unknown };
  /** Serializer's provenance field — `'stub'`/`'safe_default'` means no real proposal. */
  model_used: string;
  /** False when the cascade fell back to the deterministic safe problem. */
  ai_available: boolean;
  /** True when a real LLM answer was deterministically snapped onto the grid. */
  repaired: boolean;
  /** PV-1's verdict code for the returned problem (e.g. `'ok'`, `'ok_variable'`, `'safe_default'`). */
  verdict_code: string;
  /**
   * PV-5: validated sampling ranges for a randomized `{{var}}` answer,
   * verified reachable for every sampled student. `{}` when the problem is
   * static (flag off, the AI chose a concrete value, or the safe default).
   */
  variable_constraints: Record<string, PracticeVariableConstraint>;
}

const proposeProblem = async (
  data: PracticeProblemRequest,
): Promise<PracticeProblemResponse> => {
  const response = await apiClient.post<PracticeProblemResponse>(
    '/ai/practice-problem/',
    data,
  );
  return response.data;
};

export const usePracticeProblem = () =>
  useMutation<PracticeProblemResponse, Error, PracticeProblemRequest>({
    mutationFn: proposeProblem,
  });
