/**
 * Tests for the widgets registry barrel (IW-1c).
 *
 * The registry is the only place the host learns which kinds it can render
 * — its shape (keys are valid kinds, values are well-typed modules) is the
 * single source of truth. Cover the shape, the `_hello` reference module,
 * and the `getWidgetModule` lookup contract.
 */

import { describe, expect, it } from 'vitest';
import { getWidgetModule, widgetRegistry } from './registry';

describe('widgetRegistry', () => {
  it('exposes the _hello reference widget', () => {
    expect(widgetRegistry._hello).toBeDefined();
    expect(widgetRegistry._hello.kind).toBe('_hello');
    expect(widgetRegistry._hello.version).toBeGreaterThan(0);
    expect(widgetRegistry._hello.meta.title).toMatch(/Hello/);
  });

  it('every entry round-trips its registry key into module.kind', () => {
    for (const [key, mod] of Object.entries(widgetRegistry)) {
      expect(mod.kind).toBe(key);
    }
  });
});

describe('getWidgetModule', () => {
  it('returns the module for a known kind', () => {
    const m = getWidgetModule('_hello');
    expect(m).toBeDefined();
    expect(m!.kind).toBe('_hello');
  });

  it('returns undefined for an unknown kind (so the host can render an error state)', () => {
    expect(getWidgetModule('not-a-real-widget')).toBeUndefined();
    expect(getWidgetModule('')).toBeUndefined();
  });
});
