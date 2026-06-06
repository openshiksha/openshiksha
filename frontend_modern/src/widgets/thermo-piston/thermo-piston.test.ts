/**
 * Tests for the `thermo-piston` widget module (IW-2).
 *
 * We test the *module surface* (the WidgetModule returned by
 * `defineWidget`), not the in-sandbox render — that runs inside the
 * iframe and is exercised end-to-end by the host srcdoc tests + Playwright.
 * The render-source string is what the runtime boot inlines, so its
 * contents are the wire contract for what this widget actually does.
 */

import { describe, expect, it } from 'vitest';
import thermoPiston from './index';
import { getWidgetModule } from '../registry';

describe('thermo-piston widget module', () => {
  it('declares the expected identity + version', () => {
    expect(thermoPiston.kind).toBe('thermo-piston');
    expect(thermoPiston.version).toBe(1);
  });

  it('is explanatory (no answer-producing flag)', () => {
    expect(thermoPiston.meta.answerProducing).toBe(false);
  });

  it('is registered in the SDK registry under its kind key', () => {
    const lookup = getWidgetModule('thermo-piston');
    expect(lookup).toBe(thermoPiston);
  });

  it('renderSource is a self-contained function expression (the runtime inlines it as-is)', () => {
    // Sanity: stringified render starts with the function arrow head or
    // function keyword and references its parameter through `ctx` properties.
    expect(thermoPiston.renderSource).toMatch(/^\s*(\(|function|ctx)/);
    expect(thermoPiston.renderSource).toContain('mount');
    expect(thermoPiston.renderSource).toContain('config');
    expect(thermoPiston.renderSource).toContain('variables');
  });

  it('renderSource bakes in the First-Law physics and the legacy slider bounds', () => {
    // Spot-check the physics readout copy + default bound numbers — they
    // are the visible product surface students see.
    expect(thermoPiston.renderSource).toContain('ΔU = ΔQ − ΔW');
    expect(thermoPiston.renderSource).toContain('heatMin');
    expect(thermoPiston.renderSource).toContain('heatMax');
    expect(thermoPiston.renderSource).toContain('workMax');
    // Defaults: ±200 J — match the legacy jQuery-UI slider min/max.
    expect(thermoPiston.renderSource).toContain('200');
  });

  it('renderSource does NOT pull in jQuery or any legacy vendor surface', () => {
    expect(thermoPiston.renderSource).not.toMatch(/jquery/i);
    expect(thermoPiston.renderSource).not.toMatch(/\$\(/);
    expect(thermoPiston.renderSource).not.toMatch(/glyphicon/i);
  });

  it('animates kinetic-theory particles whose amplitude scales with ΔU = ΔQ − ΔW', () => {
    // The particle loop + the energy → amplitude mapping must end up in
    // the inlined source — that is the "hot gas vibrates harder" affordance.
    expect(thermoPiston.renderSource).toContain('requestAnimationFrame');
    expect(thermoPiston.renderSource).toContain('energyAmplitude');
    // u = q - w (internal energy) drives the amplitude normalisation.
    expect(thermoPiston.renderSource).toMatch(/q\s*-\s*w/);
  });

  it('clamps the piston so it cannot dip below the cylinder floor', () => {
    // PISTON_Y_MAX is the hard floor — without it the slab could clip
    // through the cylinder wall on extreme negative work. The 36 px gas
    // floor below it is the matching invariant the particle loop relies on.
    expect(thermoPiston.renderSource).toContain('PISTON_Y_MAX');
    expect(thermoPiston.renderSource).toContain('PISTON_Y_MIN');
    // Math.max with the floor of 36 keeps gasH from collapsing to zero.
    expect(thermoPiston.renderSource).toMatch(/Math\.max\(36,/);
  });
});
