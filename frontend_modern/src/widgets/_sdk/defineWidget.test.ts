/**
 * Tests for the `defineWidget` factory (IW-1c).
 *
 * The factory is the Tier-3 authoring entry point — every widget kind goes
 * through it, so validation needs to be loud (fail-throw) rather than
 * silent. Cover the happy path and every rejection branch.
 */

import { describe, expect, it } from 'vitest';
import { defineWidget } from './defineWidget';

describe('defineWidget', () => {
  it('returns a module with kind/version/meta and a stringified renderSource', () => {
    const m = defineWidget({
      kind: 'unit-test',
      version: 2,
      meta: { title: 'Tester', answerProducing: true },
      render: (ctx) => {
        ctx.mount.textContent = 'hi';
      },
    });
    expect(m.kind).toBe('unit-test');
    expect(m.version).toBe(2);
    expect(m.meta.title).toBe('Tester');
    expect(m.meta.answerProducing).toBe(true);
    expect(typeof m.renderSource).toBe('string');
    // The stringified source contains the body so the runtime boot can
    // wrap it. Don't pin the exact text because bundlers may rename
    // parameters; just assert the function body content is present.
    expect(m.renderSource).toContain('mount');
    expect(m.renderSource).toContain('hi');
  });

  it('rejects an empty kind', () => {
    expect(() =>
      defineWidget({
        kind: '',
        version: 1,
        meta: { title: 't' },
        render: () => undefined,
      }),
    ).toThrow(/kind/);
  });

  it('rejects a non-positive version', () => {
    expect(() =>
      defineWidget({
        kind: 'x',
        version: 0,
        meta: { title: 't' },
        render: () => undefined,
      }),
    ).toThrow(/version/);
  });

  it('rejects a non-integer version', () => {
    expect(() =>
      defineWidget({
        kind: 'x',
        version: 1.5,
        meta: { title: 't' },
        render: () => undefined,
      }),
    ).toThrow(/version/);
  });

  it('rejects a missing render function', () => {
    expect(() =>
      defineWidget({
        kind: 'x',
        version: 1,
        meta: { title: 't' },
        // @ts-expect-error — intentionally bad
        render: 'not a function',
      }),
    ).toThrow(/render/);
  });

  it('rejects a missing meta.title', () => {
    expect(() =>
      defineWidget({
        kind: 'x',
        version: 1,
        // @ts-expect-error — intentionally bad
        meta: {},
        render: () => undefined,
      }),
    ).toThrow(/meta\.title/);
  });
});
