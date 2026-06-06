/**
 * Tests for the `function-plotter` widget module (IW-6).
 *
 * Module-surface coverage. In-iframe rendering of the actual SVG
 * polyline is exercised end-to-end by `/design` and Playwright; here
 * we pin the render-source contents so a refactor can't silently drop
 * the in-sandbox parser or its safe-function whitelist.
 */

import { describe, expect, it } from 'vitest';
import functionPlotter from './index';
import { getWidgetModule } from '../registry';

describe('function-plotter widget module', () => {
  it('declares the expected identity + version', () => {
    expect(functionPlotter.kind).toBe('function-plotter');
    expect(functionPlotter.version).toBe(1);
  });

  it('is explanatory (no answer-producing flag)', () => {
    expect(functionPlotter.meta.answerProducing).toBe(false);
  });

  it('is registered in the SDK registry under its kind key', () => {
    expect(getWidgetModule('function-plotter')).toBe(functionPlotter);
  });

  it('ships a paramsSchema for the gallery form (IW-5)', () => {
    expect(functionPlotter.paramsSchema).toBeDefined();
    const props = (functionPlotter.paramsSchema as { properties?: Record<string, unknown> })
      .properties;
    expect(props && 'expr' in props).toBe(true);
    expect(props && 'xMin' in props).toBe(true);
    expect(props && 'xMax' in props).toBe(true);
  });

  it('renderSource uses a parser, not Function() or eval()', () => {
    // The whole point of the hand-rolled parser is to keep eval/Function
    // out of widget source so contributors copying from this file don't
    // ship the dangerous pattern. Pin that invariant.
    expect(functionPlotter.renderSource).not.toMatch(/\beval\s*\(/);
    expect(functionPlotter.renderSource).not.toMatch(/\bnew Function\b/);
    expect(functionPlotter.renderSource).toContain('tokenise');
    expect(functionPlotter.renderSource).toContain('parseAdd');
  });

  it('renderSource whitelists the math curriculum function set', () => {
    // Spot-check a handful from each arity so an accidental drop of the
    // UNARY/BINARY map is loud.
    for (const fn of ['sin', 'cos', 'log', 'ln', 'sqrt', 'abs']) {
      expect(functionPlotter.renderSource).toContain(fn);
    }
    expect(functionPlotter.renderSource).toMatch(/\bpow\b/);
  });

  it('renderSource handles bad expressions with a friendly error band', () => {
    // Compile errors must never crash the widget; pin the surface.
    expect(functionPlotter.renderSource).toContain('Could not plot');
  });
});
