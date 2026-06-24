/**
 * Tests for the in-sandbox deterministic algebraic-equivalence engine (GSV-2a).
 *
 * This is the JS counterpart of the backend `apps/core/tests/test_algebra.py`,
 * and it mirrors that suite's coverage one-to-one so the two engines can never
 * silently diverge: the **real path** (correct equivalence verdicts across the
 * curriculum's expression/equation forms) and the **deterministic fallback**
 * (malformed input never throws — it returns a verdict with a populated
 * `error`). No AI, no network, no DOM: the engine is pure and seeded, so every
 * assertion is reproducible.
 */

import { describe, expect, it } from 'vitest';
import {
  areEquationsEquivalent,
  areExpressionsEquivalent,
  checkStep,
  isTrustworthy,
  type EquivalenceResult,
} from './algebra';

// --------------------------------------------------------------------------- //
// Expression equivalence — the real path
// --------------------------------------------------------------------------- //

describe('expression equivalence', () => {
  const equivalent: [string, string][] = [
    ['2*(x + 3)', '2*x + 6'], // distribution
    ['x + x', '2*x'], // like terms
    ['(x + 1)^2', 'x^2 + 2*x + 1'], // binomial expansion
    ['x*x*x', 'x^3'], // powers
    ['3*x - x', '2*x'], // subtraction
    ['(x^2 - 1)/(x - 1)', 'x + 1'], // rational simplification (x != 1)
    ['x + y', 'y + x'], // commutativity, two vars
    ['2*x*y + x*y', '3*x*y'], // multi-variable
    ['6/2', '3'], // constants
    ['sin(x)^2 + cos(x)^2', '1'], // trig identity
  ];
  it.each(equivalent)('treats %s ≡ %s as equivalent', (a, b) => {
    const result = areExpressionsEquivalent(a, b);
    expect(result.equivalent, `${a} != ${b}: ${result.reason}`).toBe(true);
    expect(isTrustworthy(result)).toBe(true);
  });

  it('parses implicit multiplication the way students write it', () => {
    // A coefficient or a group juxtaposed with a factor parses as a product
    // (2x, 3(x+1), x(x+1)). A multi-letter run is a single identifier (so
    // function names like `sin` keep working), not a product of single letters —
    // an intentional limitation matching the backend engine.
    expect(areExpressionsEquivalent('2x + 6', '2*(x+3)').equivalent).toBe(true);
    expect(areExpressionsEquivalent('3(x+1)', '3x + 3').equivalent).toBe(true);
    expect(areExpressionsEquivalent('x(x+1)', 'x^2 + x').equivalent).toBe(true);
  });

  const inequivalent: [string, string][] = [
    ['2*x + 6', '2*x + 5'], // off by a constant
    ['x + x', 'x^2'], // different growth
    ['(x + 1)^2', 'x^2 + 1'], // dropped cross term
    ['x + y', 'x - y'], // sign
    ['2', '3'], // different constants
  ];
  it.each(inequivalent)('treats %s ≠ %s as inequivalent', (a, b) => {
    const result = areExpressionsEquivalent(a, b);
    expect(result.equivalent, `${a} == ${b}? ${result.reason}`).toBe(false);
    expect(isTrustworthy(result)).toBe(true); // a real verdict, not a parse error
  });

  it('reports a constant divide-by-zero as a verdict, not a crash', () => {
    // 1/0 is non-finite for a constant expression -> fallback, not a throw.
    const result = areExpressionsEquivalent('1/0', 'x');
    expect(result.equivalent).toBe(false);
  });
});

// --------------------------------------------------------------------------- //
// Equation equivalence — the real path
// --------------------------------------------------------------------------- //

describe('equation equivalence', () => {
  const equivalent: [string, string][] = [
    ['2*x = 6', 'x = 3'], // divide both sides
    ['x + 3 = 7', 'x = 4'], // subtract from both sides
    ['2*x = 6', '4*x - 12 = 0'], // rearrange + scale
    ['3*x + 1 = 10', '3*x = 9'], // subtract constant
    ['x/2 = 4', 'x = 8'], // multiply both sides
    ['2x + 4 = 10', 'x = 3'], // implicit mult, full solve
    ['y = 2*x + 1', 'y - 1 = 2*x'], // two-variable rearrange
  ];
  it.each(equivalent)('treats %s ~ %s as equivalent', (a, b) => {
    const result = areEquationsEquivalent(a, b);
    expect(result.equivalent, `${a} !~ ${b}: ${result.reason}`).toBe(true);
    expect(isTrustworthy(result)).toBe(true);
  });

  const inequivalent: [string, string][] = [
    ['2*x = 6', 'x = 4'], // wrong solution
    ['x + 3 = 7', 'x = 5'], // arithmetic slip
    ['2*x = 6', 'x = -3'], // sign error
    ['3*x = 9', '3*x = 12'], // different constant
  ];
  it.each(inequivalent)('treats %s !~ %s as inequivalent', (a, b) => {
    const result = areEquationsEquivalent(a, b);
    expect(result.equivalent, `${a} ~ ${b}? ${result.reason}`).toBe(false);
    expect(isTrustworthy(result)).toBe(true);
  });

  it('recognises identities, but not as equal to a real constraint', () => {
    expect(areEquationsEquivalent('0 = 0', '2 - 2 = 0').equivalent).toBe(true);
    expect(areEquationsEquivalent('0 = 0', 'x = 1').equivalent).toBe(false);
  });

  it('rejects a non-equation input with an error', () => {
    const result = areEquationsEquivalent('x + 1', 'x = 1');
    expect(result.equivalent).toBe(false);
    expect(result.error).not.toBeNull();
  });
});

// --------------------------------------------------------------------------- //
// checkStep dispatch + the deterministic fallback
// --------------------------------------------------------------------------- //

describe('checkStep dispatch', () => {
  it('dispatches a pair of equations to the equation checker', () => {
    expect(checkStep('2*x = 6', 'x = 3').equivalent).toBe(true);
    expect(checkStep('2*x = 6', 'x = 4').equivalent).toBe(false);
  });

  it('dispatches a pair of bare expressions to the expression checker', () => {
    expect(checkStep('2*(x + 1)', '2*x + 2').equivalent).toBe(true);
    expect(checkStep('2*(x + 1)', '2*x + 3').equivalent).toBe(false);
  });

  it('rejects a mixed equation/expression pair', () => {
    const result = checkStep('x = 3', 'x + 0');
    expect(result.equivalent).toBe(false);
    expect(result.error).not.toBeNull();
  });

  const malformed: [string, string][] = [
    ['2*(x +', '2*x'], // unbalanced parens
    ['x @ 2', 'x'], // illegal character
    ['', 'x'], // empty line
    ['x', '   '], // whitespace-only line
    ['x = = 3', 'x = 3'], // multiple '='
  ];
  it.each(malformed)('returns an error verdict (never throws) for %s → %s', (prev, cur) => {
    // The deterministic fallback: a structured non-equivalent result with an
    // error message, never an exception bubbling into the caller.
    const result = checkStep(prev, cur);
    expect(result.equivalent).toBe(false);
    expect(result.error).not.toBeNull();
  });

  it('guards non-string input', () => {
    const result = checkStep(null, 'x');
    expect(result.equivalent).toBe(false);
    expect(result.error).not.toBeNull();
  });

  it('populates a deterministic, human-readable reason on every verdict', () => {
    const ok = checkStep('2*x = 6', 'x = 3');
    expect(ok.reason).toBeTruthy();
    const bad = checkStep('2*x = 6', 'x = 4');
    expect(bad.reason).toBeTruthy();
  });
});

// --------------------------------------------------------------------------- //
// Determinism — the seeded probing yields the same verdict every call
// --------------------------------------------------------------------------- //

describe('determinism', () => {
  it('returns identical verdicts for identical inputs across repeated calls', () => {
    const verdicts = new Set<boolean>();
    const reasons = new Set<string>();
    for (let i = 0; i < 5; i += 1) {
      const r: EquivalenceResult = areExpressionsEquivalent('(x+1)^2', 'x^2 + 2x + 1');
      expect(r.equivalent).toBe(true);
      expect(areExpressionsEquivalent('(x+1)^2', 'x^2 + 1').equivalent).toBe(false);
      verdicts.add(r.equivalent);
      reasons.add(r.reason);
    }
    // Same verdict and same reason every time — seeded, reproducible.
    expect(verdicts.size).toBe(1);
    expect(reasons.size).toBe(1);
  });
});
