import { describe, it, expect, beforeAll } from 'vitest';
import { en } from './locales/en';
import { LOCALES, localeLoaders, type Locale } from './locales/registry';

/**
 * LA-5 → LA-9a parity guard, now registry-driven with a pilot-coverage model.
 *
 * For every registered non-English locale we load its dictionary and apply a
 * contract that depends on its declared `coverage`:
 *
 * - `complete` (en, hi): exact key-set parity with English — no missing keys,
 *   no extra keys — and no blank strings.
 * - `pilot` (e.g. mr): a *subset* is allowed (English fills the gaps at
 *   runtime, principle 3), but every key it *does* define must (i) exist in
 *   English and (ii) match English's `{var}` placeholders, and never be blank.
 *
 * Key parity for `complete` locales is also tsc-enforced (`LocaleDict`); this
 * runtime test fails with a readable list of the drifted keys and checks what
 * the type system can't (placeholder drift, blanks, pilot subset validity).
 * Runs in the normal vitest gate — no CI pipeline changes.
 */

const placeholdersOf = (template: string): string[] =>
  [...template.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();

const enKeys = Object.keys(en);
const enKeySet = new Set(enKeys);

type Dict = Partial<Record<string, string>>;

// Load every non-English dictionary once (en is the eager source of truth).
const dicts: Partial<Record<Locale, Dict>> = { en };

beforeAll(async () => {
  for (const meta of LOCALES) {
    if (meta.code === 'en') continue;
    const load = localeLoaders[meta.code];
    expect(load, `locale "${meta.code}" is registered but has no loader`).toBeTruthy();
    const module = (await load!()) as Record<string, Dict | undefined>;
    const dict = module[meta.code] ?? (module.default as Dict | undefined);
    expect(dict, `loader for "${meta.code}" must export a dictionary`).toBeTruthy();
    dicts[meta.code] = dict!;
  }
});

describe('locale key parity (registry-driven, pilot-coverage)', () => {
  for (const meta of LOCALES) {
    if (meta.code === 'en') continue;

    describe(`${meta.code} (${meta.coverage})`, () => {
      it('defines only keys that exist in English', () => {
        const extra = Object.keys(dicts[meta.code]!).filter((k) => !enKeySet.has(k));
        expect(extra, `keys in ${meta.code}.ts but not en.ts: ${extra.join(', ')}`).toEqual([]);
      });

      it('has no blank strings', () => {
        const blank = Object.entries(dicts[meta.code]!)
          .filter(([, v]) => (v ?? '').trim() === '')
          .map(([k]) => k);
        expect(blank, `blank strings in ${meta.code}.ts: ${blank.join(', ')}`).toEqual([]);
      });

      it('matches English interpolation placeholders for every key it defines', () => {
        const dict = dicts[meta.code]!;
        const mismatches = Object.keys(dict)
          .filter((k) => enKeySet.has(k))
          .map((k) => ({
            key: k,
            en: placeholdersOf(en[k as keyof typeof en]),
            loc: placeholdersOf(dict[k] as string),
          }))
          .filter(({ en: a, loc: b }) => JSON.stringify(a) !== JSON.stringify(b));

        expect(
          mismatches,
          `placeholder drift in ${meta.code}: ${mismatches
            .map((m) => `${m.key} (en: {${m.en}} vs ${meta.code}: {${m.loc}})`)
            .join('; ')}`,
        ).toEqual([]);
      });

      if (meta.coverage === 'complete') {
        it('has exact key-set parity with English (complete coverage)', () => {
          const missing = enKeys.filter((k) => !(k in dicts[meta.code]!));
          expect(
            missing,
            `keys missing from ${meta.code}.ts: ${missing.join(', ')}`,
          ).toEqual([]);
        });
      }
    });
  }
});
