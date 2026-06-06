/**
 * Tests for the Widgets Framework protocol types (IW-1a).
 *
 * The guards are the public boundary every host/runtime check goes through —
 * a regression here would silently break the `event.source` security model in
 * host.ts (IW-1b). Cover positive matches, version mismatches, and structural
 * garbage.
 */

import { describe, expect, it } from 'vitest';
import {
  isErrorMessage,
  isInitMessage,
  isReadyMessage,
  isResizeMessage,
  isValueMessage,
  isWidgetMessage,
  WIDGET_PROTOCOL_VERSION,
} from './protocol';

describe('WIDGET_PROTOCOL_VERSION', () => {
  it('is a positive integer that both sides pin against', () => {
    expect(Number.isInteger(WIDGET_PROTOCOL_VERSION)).toBe(true);
    expect(WIDGET_PROTOCOL_VERSION).toBeGreaterThan(0);
  });
});

describe('isInitMessage', () => {
  it('accepts a well-formed init', () => {
    expect(
      isInitMessage({
        type: 'init',
        protocol: WIDGET_PROTOCOL_VERSION,
        kind: 'thermo-piston',
        config: { initialVolume: 5 },
        variables: { a: 5 },
        imageBase: 'https://example.com/',
      }),
    ).toBe(true);
  });

  it('rejects messages from a different protocol version', () => {
    expect(
      isInitMessage({
        type: 'init',
        protocol: WIDGET_PROTOCOL_VERSION + 1,
        kind: 'x',
        config: {},
        variables: {},
        imageBase: '',
      }),
    ).toBe(false);
  });

  it('rejects null and primitives', () => {
    expect(isInitMessage(null)).toBe(false);
    expect(isInitMessage(undefined)).toBe(false);
    expect(isInitMessage('init')).toBe(false);
    expect(isInitMessage(42)).toBe(false);
  });
});

describe('widget → host guards', () => {
  const base = { protocol: WIDGET_PROTOCOL_VERSION } as const;

  it('isReadyMessage matches ready', () => {
    expect(isReadyMessage({ ...base, type: 'ready' })).toBe(true);
    expect(isReadyMessage({ ...base, type: 'resize', height: 100 })).toBe(false);
  });

  it('isResizeMessage requires a numeric height', () => {
    expect(isResizeMessage({ ...base, type: 'resize', height: 120 })).toBe(true);
    expect(isResizeMessage({ ...base, type: 'resize' })).toBe(false);
    expect(isResizeMessage({ ...base, type: 'resize', height: '120' })).toBe(false);
  });

  it('isValueMessage accepts any value payload', () => {
    expect(isValueMessage({ ...base, type: 'value', value: 42 })).toBe(true);
    expect(isValueMessage({ ...base, type: 'value', value: { a: [1, 2] } })).toBe(true);
    expect(isValueMessage({ ...base, type: 'value', value: null })).toBe(true);
  });

  it('isErrorMessage requires a string message', () => {
    expect(isErrorMessage({ ...base, type: 'error', message: 'boom' })).toBe(true);
    expect(isErrorMessage({ ...base, type: 'error' })).toBe(false);
    expect(isErrorMessage({ ...base, type: 'error', message: 42 })).toBe(false);
  });

  it('isWidgetMessage rejects host-bound messages', () => {
    expect(
      isWidgetMessage({
        ...base,
        type: 'init',
        kind: 'x',
        config: {},
        variables: {},
        imageBase: '',
      }),
    ).toBe(false);
  });

  it('isWidgetMessage rejects garbage', () => {
    expect(isWidgetMessage({})).toBe(false);
    expect(isWidgetMessage(null)).toBe(false);
    expect(isWidgetMessage({ ...base, type: 'unknown' })).toBe(false);
  });
});
