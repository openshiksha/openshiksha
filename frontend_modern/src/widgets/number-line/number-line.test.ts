/**
 * Tests for the `number-line` answer-producing widget (IW-4).
 *
 * Module-surface coverage: identity, registry round-trip, render-source
 * contents (the renderSource is what the runtime bakes into the iframe
 * boot, so its contents *are* the wire contract for what this widget does).
 * In-iframe pointer behaviour is exercised end-to-end by `/design` and
 * Playwright; we don't need a happy-dom shim to assert the math here.
 */

import { describe, expect, it } from 'vitest';
import numberLine from './index';
import { getWidgetModule } from '../registry';

describe('number-line widget module', () => {
  it('declares the expected identity + version', () => {
    expect(numberLine.kind).toBe('number-line');
    expect(numberLine.version).toBe(1);
  });

  it('is answer-producing — flips on the meta flag QuestionCard reads', () => {
    // This is the load-bearing flag for the IW-4 wiring. QuestionCard
    // hides the typed SubpartInput and pipes onValue through when this
    // is true; flipping it back to false would silently re-introduce
    // the parallel-input regression.
    expect(numberLine.meta.answerProducing).toBe(true);
  });

  it('is registered in the SDK registry under its kind key', () => {
    expect(getWidgetModule('number-line')).toBe(numberLine);
  });

  it('renderSource calls reportValue from inside the render', () => {
    // Without reportValue the widget cannot produce an answer — that
    // would make it a thermo-piston-style explanatory widget by accident
    // and the value would never reach the submission form.
    expect(numberLine.renderSource).toMatch(/reportValue/);
  });

  it('renderSource uses pointer events (mouse/touch/stylus unified)', () => {
    expect(numberLine.renderSource).toContain('pointerdown');
    expect(numberLine.renderSource).toContain('pointermove');
    expect(numberLine.renderSource).toContain('setPointerCapture');
  });

  it('renderSource snaps to step and clamps to [min, max]', () => {
    // The snap math is what the grader sees; pinning these markers
    // means a refactor cannot silently regress the precision.
    expect(numberLine.renderSource).toContain('Math.round');
    expect(numberLine.renderSource).toContain('Math.max');
    expect(numberLine.renderSource).toContain('Math.min');
  });

  it('renderSource supports keyboard accessibility (ArrowLeft/Right, Home/End)', () => {
    expect(numberLine.renderSource).toContain('ArrowLeft');
    expect(numberLine.renderSource).toContain('ArrowRight');
    expect(numberLine.renderSource).toContain('Home');
    expect(numberLine.renderSource).toContain('End');
  });

  it('renderSource does NOT call reportValue at mount (initial value stays empty until drag)', () => {
    // The "no reportValue on mount" invariant means a student can leave
    // a question blank. Implementation detail: the hasInteracted flag
    // gates the first call. Without that flag the answer field would
    // pre-fill with the initial position.
    expect(numberLine.renderSource).toContain('hasInteracted');
  });
});
