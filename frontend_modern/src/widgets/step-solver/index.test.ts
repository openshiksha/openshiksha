/**
 * Tests for the `step-solver` answer-producing widget (GSV-2b).
 *
 * Three layers:
 *
 *  1. **Module surface** — identity, version, `answerProducing`, registry
 *     round-trip, and renderSource markers (the renderSource is the wire
 *     contract the runtime bakes into the sandbox).
 *  2. **Executed render** — drive the real `render` against a happy-dom DOM:
 *     type a correct step → ✓ and `reportValue(finalLine)`; type a wrong step →
 *     ✗ (but the line is still reported — the grade is deterministic and lives
 *     in the per-subpart grader, not here); malformed input never throws;
 *     Enter / "Add step" grow the rows up to `maxLines`.
 *  3. **Anti-drift parity** — the live ✓/✗ the inlined sandbox engine produces
 *     must match `checkStep` from `./algebra.ts` (the tested single source,
 *     itself the port of `apps/core/algebra.py`) for every line pair. This is
 *     the guard that the inlined copy can never silently diverge from the
 *     canonical engine.
 */

import { afterEach, describe, expect, it, vi } from 'vitest';
import stepSolver, { render } from './index';
import { getWidgetModule } from '../registry';
import { checkStep } from './algebra';
import type { WidgetContext } from '../_sdk/defineWidget';

describe('step-solver widget module', () => {
  it('declares the expected identity + version', () => {
    expect(stepSolver.kind).toBe('step-solver');
    expect(stepSolver.version).toBe(1);
  });

  it('is answer-producing — the final line flows into the grader', () => {
    expect(stepSolver.meta.answerProducing).toBe(true);
  });

  it('is registered in the SDK registry under its kind key', () => {
    expect(getWidgetModule('step-solver')).toBe(stepSolver);
  });

  it('renderSource calls reportValue (the answer reaches the form)', () => {
    expect(stepSolver.renderSource).toMatch(/reportValue/);
  });

  it('renderSource contains the deterministic engine, NOT eval/Function/AI', () => {
    // The live check must be the deterministic numeric-probing engine, inlined
    // in the sandbox — never code-eval, never a network/AI call.
    expect(stepSolver.renderSource).toContain('mulberry32');
    expect(stepSolver.renderSource).toContain('checkStep');
    expect(stepSolver.renderSource).not.toMatch(/\beval\b/);
    expect(stepSolver.renderSource).not.toMatch(/new Function/);
    expect(stepSolver.renderSource).not.toMatch(/fetch\(/);
  });
});

// ── Executed-render harness ────────────────────────────────────────────────

interface Harness {
  mount: HTMLElement;
  reportValue: ReturnType<typeof vi.fn>;
  /** All student step inputs currently in the DOM, top to bottom. */
  inputs: () => HTMLInputElement[];
  /** The ✓/✗ marks for the student rows, top to bottom. */
  marks: () => HTMLElement[];
  addButton: () => HTMLButtonElement;
}

function mountWidget(config: Record<string, unknown>): Harness {
  const mount = document.createElement('div');
  document.body.appendChild(mount);
  const reportValue = vi.fn();
  const ctx: WidgetContext = {
    mount,
    config,
    variables: {},
    imageBase: '',
    reportValue,
    requestResize: vi.fn(),
  };
  render(ctx);
  return {
    mount,
    reportValue,
    inputs: () => Array.from(mount.querySelectorAll<HTMLInputElement>('input.ss-input')),
    marks: () => Array.from(mount.querySelectorAll<HTMLElement>('.ss-mark[role="img"]')),
    addButton: () => mount.querySelector('button.ss-add') as HTMLButtonElement,
  };
}

/** Type `text` into a student input and fire the `input` event the widget listens for. */
function typeInto(input: HTMLInputElement, text: string): void {
  input.value = text;
  input.dispatchEvent(new Event('input', { bubbles: true }));
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('step-solver render — live check + answer reporting', () => {
  it('shows the prompt and starts with one empty step (no report at mount)', () => {
    const h = mountWidget({ prompt: '2x + 1 = 7', label: 'Solve for x' });
    expect(h.mount.querySelector('.ss-prompt')?.textContent).toBe('2x + 1 = 7');
    expect(h.mount.querySelector('.ss-label')?.textContent).toBe('Solve for x');
    expect(h.inputs()).toHaveLength(1);
    // The number-line invariant: nothing is reported until the student types.
    expect(h.reportValue).not.toHaveBeenCalled();
  });

  it('marks an equivalent step ✓ and reports the line', () => {
    const h = mountWidget({ prompt: '2x + 1 = 7' });
    typeInto(h.inputs()[0], '2x = 6'); // subtract 1 from both sides — valid
    expect(h.marks()[0].getAttribute('data-state')).toBe('ok');
    expect(h.marks()[0].textContent).toBe('✓');
    expect(h.reportValue).toHaveBeenLastCalledWith('2x = 6');
  });

  it('marks a non-equivalent step ✗ but STILL reports it (grade is deterministic + external)', () => {
    const h = mountWidget({ prompt: '2x + 1 = 7' });
    typeInto(h.inputs()[0], '2x = 8'); // wrong: changes the solution
    expect(h.marks()[0].getAttribute('data-state')).toBe('bad');
    expect(h.marks()[0].textContent).toBe('✗');
    // The widget reports whatever the student wrote; correctness is graded
    // elsewhere (AI is nowhere near, and neither is the live ✗ marker).
    expect(h.reportValue).toHaveBeenLastCalledWith('2x = 8');
  });

  it('never throws on a malformed line — neutral fallback, not a crash', () => {
    const h = mountWidget({ prompt: '2x + 1 = 7' });
    expect(() => typeInto(h.inputs()[0], '2x = )(')).not.toThrow();
    expect(h.marks()[0].getAttribute('data-state')).toBe('neutral');
  });

  it('checks expression prompts too (no =) via implicit multiplication', () => {
    const h = mountWidget({ prompt: '2(x + 3)' });
    typeInto(h.inputs()[0], '2x + 6'); // distribute — equivalent expression
    expect(h.marks()[0].getAttribute('data-state')).toBe('ok');
  });

  it('grows rows on Enter and reports the LAST non-empty line as the answer', () => {
    const h = mountWidget({ prompt: '2x + 1 = 7' });
    const first = h.inputs()[0];
    typeInto(first, '2x = 6');
    first.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    expect(h.inputs()).toHaveLength(2);
    typeInto(h.inputs()[1], 'x = 3'); // divide by 2 — valid final answer
    expect(h.marks()[1].getAttribute('data-state')).toBe('ok');
    expect(h.reportValue).toHaveBeenLastCalledWith('x = 3');
  });

  it('caps student rows at maxLines', () => {
    const h = mountWidget({ prompt: 'x = 1', maxLines: 2 });
    typeInto(h.inputs()[0], 'x = 1');
    h.addButton().click();
    expect(h.inputs()).toHaveLength(2);
    typeInto(h.inputs()[1], 'x = 1');
    // At the cap now — the add button is disabled and no third row appears.
    expect(h.addButton().disabled).toBe(true);
    h.addButton().click();
    expect(h.inputs()).toHaveLength(2);
  });
});

// ── Anti-drift parity with the canonical algebra.ts engine ──────────────────

describe('step-solver inlined engine matches algebra.ts (no drift)', () => {
  // A battery spanning the curriculum forms + malformed inputs. For each, the
  // on-screen ✓/✗ the *inlined* engine renders must equal `checkStep` from the
  // canonical `algebra.ts`. If the two ever diverge, this fails loudly.
  const PROMPT_STEP_PAIRS: ReadonlyArray<readonly [string, string]> = [
    // equations — valid moves
    ['2x + 1 = 7', '2x = 6'],
    ['2x = 6', 'x = 3'],
    ['3(x + 2) = 12', '3x + 6 = 12'],
    ['x/2 = 4', 'x = 8'],
    ['x + x = 10', '2x = 10'],
    // equations — invalid moves
    ['2x + 1 = 7', '2x = 8'],
    ['2x = 6', 'x = 4'],
    ['x + 3 = 5', 'x = 1'],
    // expressions — equivalent
    ['2(x + 3)', '2x + 6'],
    ['(x + 1)^2', 'x^2 + 2x + 1'],
    ['x*x*x', 'x^3'],
    // expressions — not equivalent
    ['2(x + 3)', '2x + 3'],
    ['(x + 1)^2', 'x^2 + 1'],
    // identities + constants
    ['x = x', '2x = 2x'],
    ['4 = 4', '2 + 2 = 4'],
    // mixed / malformed (error path → algebra.ts returns equivalent:false)
    ['2x + 1 = 7', '2x + 6'],
    ['x + 1', 'x ='],
    ['x + 1', '(('],
  ];

  for (const [prompt, step] of PROMPT_STEP_PAIRS) {
    it(`"${prompt}" → "${step}" agrees with checkStep`, () => {
      const expected = checkStep(prompt, step);
      const h = mountWidget({ prompt });
      typeInto(h.inputs()[0], step);
      const state = h.marks()[0].getAttribute('data-state');

      if (expected.error) {
        // algebra.ts hit its deterministic fallback; the widget shows neutral.
        expect(state).toBe('neutral');
      } else {
        expect(state).toBe(expected.equivalent ? 'ok' : 'bad');
      }
      document.body.innerHTML = '';
    });
  }
});
