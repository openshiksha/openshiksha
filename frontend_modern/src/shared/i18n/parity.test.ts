import { describe, it, expect } from 'vitest';
import { en } from './locales/en';
import { hi } from './locales/hi';

/**
 * LA-5 key-parity guard. Key parity is already tsc-enforced (`LocaleDict`),
 * but this runtime test fails with a readable list of the drifted keys and
 * also checks what the type system can't: that the `{var}` interpolation
 * placeholders match between locales, and that no translation is blank.
 * Runs in the normal vitest gate — no CI pipeline changes.
 */

const placeholdersOf = (template: string): string[] =>
  [...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

describe('locale key parity (en ↔ hi)', () => {
  it('en and hi have identical key sets', () => {
    const enKeys = Object.keys(en);
    const hiKeys = Object.keys(hi);
    const missingInHi = enKeys.filter((k) => !(k in hi));
    const extraInHi = hiKeys.filter((k) => !(k in en));

    expect(missingInHi, `keys missing from hi.ts: ${missingInHi.join(', ')}`).toEqual([]);
    expect(extraInHi, `keys in hi.ts but not en.ts: ${extraInHi.join(', ')}`).toEqual([]);
  });

  it('no locale string is blank', () => {
    const blankEn = Object.entries(en).filter(([, v]) => v.trim() === '');
    const blankHi = Object.entries(hi).filter(([, v]) => v.trim() === '');
    expect(blankEn.map(([k]) => k)).toEqual([]);
    expect(blankHi.map(([k]) => k)).toEqual([]);
  });

  it('interpolation placeholders match between locales', () => {
    const mismatches = Object.keys(en)
      .filter((k) => k in hi)
      .map((k) => ({
        key: k,
        en: placeholdersOf(en[k as keyof typeof en]),
        hi: placeholdersOf(hi[k as keyof typeof hi]),
      }))
      .filter(({ en: a, hi: b }) => JSON.stringify(a) !== JSON.stringify(b));

    expect(
      mismatches,
      `placeholder drift: ${mismatches.map((m) => `${m.key} (en: {${m.en}} vs hi: {${m.hi}})`).join('; ')}`,
    ).toEqual([]);
  });
});
