/**
 * DTB-5b — unit tests for the constraint-reconciliation helpers that make an
 * AI-authored widget's per-student randomisation actually persist.
 *
 * `syncVariableConstraints` is the single chokepoint that decides which
 * `{{var}}` constraints survive an edit. Pre-DTB-5b it keyed liveness off the
 * question text alone, so a token the AI bound into the *widget config* (never
 * the prose) would be dropped on the next keystroke. These tests pin the
 * widget-aware behaviour: a widget token stays alive, an orphan is pruned, and
 * existing specs (incl. AI `decimals`) are preserved verbatim.
 */

import { describe, expect, it } from 'vitest';
import {
  extractTokensFromConfig,
  syncVariableConstraints,
  type VariableSpec,
} from './createQuestionConstraints';

describe('extractTokensFromConfig', () => {
  it('finds {{var}} tokens nested anywhere in a widget config', () => {
    const tokens = extractTokensFromConfig({
      min: 0,
      max: '{{hi}}',
      label: 'Mark {{target}}',
      nested: { initial: '{{lo}}' },
    });
    expect(tokens).toEqual(['hi', 'lo', 'target']); // sorted, deduped
  });

  it('returns no tokens for a token-free config (and tolerates nullish)', () => {
    expect(extractTokensFromConfig({ min: 0, max: 10 })).toEqual([]);
    // @ts-expect-error — exercising the nullish guard at runtime
    expect(extractTokensFromConfig(undefined)).toEqual([]);
  });
});

describe('syncVariableConstraints', () => {
  const ai: VariableSpec = { min: 0, max: 1, integer: false, decimals: 2 };

  it('keeps a constraint whose token lives only in the widget config (not the text)', () => {
    // The AI bound {{target}} into the config; the prose never mentions it.
    const next = syncVariableConstraints('Plain prose, no tokens', { target: ai }, ['target']);
    expect(next).toEqual({ target: ai }); // survives — and decimals preserved
  });

  it('drops an orphan constraint with no backing token in text or widget', () => {
    const next = syncVariableConstraints('No tokens here', { stale: ai }, []);
    expect(next).toEqual({}); // pruned
  });

  it('unions text tokens and widget tokens, defaulting unseen ones', () => {
    const next = syncVariableConstraints('Compute {{a}}', { b: ai }, ['b']);
    expect(Object.keys(next).sort()).toEqual(['a', 'b']);
    // Existing spec preserved verbatim; a fresh text token gets the default.
    expect(next.b).toEqual(ai);
    expect(next.a).toEqual({ min: 1, max: 10, integer: true });
  });

  it('removing the widget (no keep-tokens) leaves only text-token constraints', () => {
    const next = syncVariableConstraints('Use {{a}}', { a: { min: 2, max: 5, integer: true }, b: ai }, []);
    expect(next).toEqual({ a: { min: 2, max: 5, integer: true } });
  });
});
