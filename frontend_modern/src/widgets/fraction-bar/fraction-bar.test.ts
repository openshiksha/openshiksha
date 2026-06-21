/**
 * Tests for the `fraction-bar` widget module (IW-6).
 *
 * Module-surface coverage; the rendered SVG is exercised end-to-end by
 * the `/design` page and the Playwright suite.
 */

import { describe, expect, it } from 'vitest';
import fractionBar from './index';
import { getWidgetModule } from '../registry';

describe('fraction-bar widget module', () => {
  it('declares the expected identity + version', () => {
    expect(fractionBar.kind).toBe('fraction-bar');
    expect(fractionBar.version).toBe(1);
  });

  it('is explanatory (no answer-producing flag)', () => {
    expect(fractionBar.meta.answerProducing).toBe(false);
  });

  it('is registered in the SDK registry under its kind key', () => {
    expect(getWidgetModule('fraction-bar')).toBe(fractionBar);
  });

  it('ships a paramsSchema for the gallery form (IW-5)', () => {
    expect(fractionBar.paramsSchema).toBeDefined();
    const props = (fractionBar.paramsSchema as { properties?: Record<string, unknown> }).properties;
    expect(props && 'numerator' in props).toBe(true);
    expect(props && 'denominator' in props).toBe(true);
    expect(props && 'mode' in props).toBe(true);
  });

  it('renderSource clamps numerator + denominator to sane bounds', () => {
    // Authoring "5/4" or "1/0" shouldn't crash the widget — pin the
    // defensive clamps that prevent the bar from going inside-out.
    expect(fractionBar.renderSource).toMatch(/Math\.max\(0/);
    expect(fractionBar.renderSource).toMatch(/Math\.max\(1/);
    expect(fractionBar.renderSource).toContain('40'); // segment cap
  });

  it('renderSource supports both shaded and labelled modes', () => {
    expect(fractionBar.renderSource).toContain('labelled');
    expect(fractionBar.renderSource).toContain('shaded');
  });

  it('renderSource uses the brand orange for shaded segments', () => {
    expect(fractionBar.renderSource).toContain('#FF6F00');
  });
});
