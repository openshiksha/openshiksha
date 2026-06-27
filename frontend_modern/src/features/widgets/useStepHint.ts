import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

/**
 * GSV-4 — Guided step-validator: the host-side **AI wrong-step explainer** call.
 *
 * Sends two successive lines of a student's working to the GSV-3 endpoint
 * `POST /ai/step-hint/`. The flagship safety property — **AI never decides
 * correctness** — is enforced *server-side*: the endpoint re-runs the
 * deterministic `apps.core.algebra.check_step` engine and only invokes the LLM
 * when that engine has *already* ruled the step wrong. So the `verdict` this
 * hook returns is always the deterministic engine's call, never the model's,
 * and the `hint` only ever explains a verdict that already exists.
 *
 * Provenance is honest:
 * - `verdict: "wrong"`, `ai_available: true`  → a real LLM explained the slip;
 *   surface the `✨ AI-generated` badge.
 * - `verdict: "wrong"`, `ai_available: false` → no key / timeout / empty output;
 *   the backend returned a deterministic static hint (`model_used: "stub"`) and
 *   the UI shows a neutral `Auto-…` badge plus a friendly "AI unavailable" line.
 * - `verdict: "correct" | "unparseable"` → the engine's own deterministic
 *   reason, `hint: null`, and the LLM was **never called**.
 *
 * This is a *host* surface (principle 1): the widget runtime is a network-less
 * sandbox, so the AI coach lives outside the iframe and consumes this endpoint.
 * It is also structurally **out of the grading path** (principle 2): it only
 * ever renders explanatory text and never reports a value to the grader.
 */

/** The deterministic engine's verdict — never the LLM's. */
export type StepHintVerdict = 'correct' | 'wrong' | 'unparseable';

export interface StepHintRequest {
  /** The line the student had correct so far. */
  previous: string;
  /** The new line the student wrote. */
  current: string;
}

export interface StepHintResponse {
  /** Always the deterministic `check_step` engine's call. */
  verdict: StepHintVerdict;
  /** The engine's deterministic reason for the verdict. */
  reason: string;
  /**
   * The AI (or static-fallback) explanation of a *wrong* step. `null` for a
   * correct or unparseable line — there is no real slip to explain, and the
   * LLM was never invoked.
   */
  hint: string | null;
  /** Serializer's provenance field — `'stub'` (or `null`) means no LLM ran. */
  model_used: string | null;
  /** False when no LLM ran (correct/unparseable, or the static-hint fallback). */
  ai_available: boolean;
}

const explainStep = async (data: StepHintRequest): Promise<StepHintResponse> => {
  const response = await apiClient.post<StepHintResponse>('/ai/step-hint/', data);
  return response.data;
};

export const useStepHint = () =>
  useMutation<StepHintResponse, Error, StepHintRequest>({
    mutationFn: explainStep,
  });
