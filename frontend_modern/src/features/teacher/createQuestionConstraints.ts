/**
 * Variable-token helpers for the question authoring page.
 *
 * Extracted from `CreateQuestionPage` so they can be unit-tested directly and
 * imported without tripping React Fast-Refresh's "components-only export" rule.
 *
 * A subpart's `variable_constraints` are the single source of truth handed to
 * the backend croupier, which samples per-student values and substitutes them
 * into both the question text and any widget config `{{var}}` tokens. Liveness
 * of a constraint therefore depends on whether its token appears in the prose
 * **or** the attached widget config (DTB-5b) — `syncVariableConstraints` is the
 * one chokepoint that enforces that union so an AI-bound widget token is never
 * silently dropped on the next text edit.
 */

// `decimals` is optional and only carried for non-integer ranges authored by
// the AI (DTB-5b); the backend croupier honours it when sampling. Text-token
// constraints edited by hand stay integer-or-2dp as before.
export type VariableSpec = { min: number; max: number; integer: boolean; decimals?: number };

export const extractTokens = (text: string): string[] => {
  const re = /\{\{(\w+)\}\}/g;
  const names = new Set<string>();
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) names.add(match[1]);
  return Array.from(names).sort();
};

// Tokens can live in the widget config too (DTB-5b), not just the question
// text, so a `{{var}}` the AI bound into a widget field stays alive even when
// it never appears in the prose.
export const extractTokensFromConfig = (config: Record<string, unknown>): string[] =>
  extractTokens(JSON.stringify(config ?? {}));

export const syncVariableConstraints = (
  text: string,
  existing: Record<string, VariableSpec>,
  keepTokens: string[] = []
): Record<string, VariableSpec> => {
  const tokens = new Set([...extractTokens(text), ...keepTokens]);
  const next: Record<string, VariableSpec> = {};
  for (const token of tokens) {
    next[token] = existing[token] ?? { min: 1, max: 10, integer: true };
  }
  return next;
};
