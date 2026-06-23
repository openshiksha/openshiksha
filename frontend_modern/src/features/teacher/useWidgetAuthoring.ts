import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

/**
 * DTB-3 — Describe-to-Build authoring call.
 *
 * Sends a plain-English description (and an optional preferred kind) to the
 * teacher-only `POST /ai/widget-authoring/` endpoint, which returns a
 * `{widget_kind, widget_config}` proposal. The proposal is **schema-valid by
 * construction** on the backend (DTB-1 validation → DTB-2 clamp-repair → safe
 * default), so the UI can drop the config straight into the existing live
 * sandbox preview + schema form without re-validating.
 *
 * Provenance is honest:
 * - `ai_available: true`  → a real LLM proposed (possibly clamp-`repaired`)
 *   the config; surface the `✨ AI-generated` badge.
 * - `ai_available: false` → the cascade was exhausted and the backend returned
 *   the kind's deterministic safe default; `model_used` is `'stub'` and the UI
 *   shows a neutral `Auto-…` badge plus a friendly "AI unavailable" line.
 */

/**
 * One per-student sampling range for a `{{var}}` token the AI bound into the
 * config (DTB-5). Mirrors the backend's reconciled constraint shape
 * (`{min, max, integer[, decimals]}`); `decimals` is present only for
 * non-integer ranges. These are schema-validated and reconciled server-side, so
 * the UI can persist them verbatim onto the subpart.
 */
export interface WidgetVariableConstraint {
  min: number;
  max: number;
  integer: boolean;
  decimals?: number;
}

export interface WidgetAuthoringRequest {
  description: string;
  /** Optional preferred widget kind the teacher already has in mind. */
  kind_hint?: string;
  /**
   * DTB-5b — opt in to per-student randomisation. When `true`, the AI may bind
   * numeric fields to croupier `{{var}}` tokens and the response carries the
   * validated `variable_constraints` to attach alongside the config.
   */
  allow_variables?: boolean;
}

export interface WidgetAuthoringResponse {
  widget_kind: string;
  widget_config: Record<string, unknown>;
  /** Serializer's provenance field — `'stub'` means no LLM ran. */
  model_used: string;
  /** False when the cascade fell back to the deterministic safe default. */
  ai_available: boolean;
  /** True when a real LLM proposal was clamp-repaired to become schema-valid. */
  repaired: boolean;
  /**
   * DTB-5: validated per-student sampling ranges for any `{{var}}` bindings in
   * the config. `{}` when the proposal isn't randomised (e.g. `allow_variables`
   * was off, or the AI chose concrete numbers).
   */
  variable_constraints: Record<string, WidgetVariableConstraint>;
}

const authorWidget = async (
  data: WidgetAuthoringRequest,
): Promise<WidgetAuthoringResponse> => {
  const response = await apiClient.post<WidgetAuthoringResponse>(
    '/ai/widget-authoring/',
    data,
  );
  return response.data;
};

export const useWidgetAuthoring = () =>
  useMutation<WidgetAuthoringResponse, Error, WidgetAuthoringRequest>({
    mutationFn: authorWidget,
  });
