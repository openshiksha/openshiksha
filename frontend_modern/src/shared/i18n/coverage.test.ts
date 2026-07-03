import { describe, it, expect, beforeAll } from 'vitest';
import { en } from './locales/en';
import { LOCALES, localeLoaders, type Locale, type LocaleMeta } from './locales/registry';

/**
 * LA-9e — pilot-coverage report.
 *
 * For each `pilot` locale, logs `<code>: N/<total> keys (<pct>%)` so a reviewer
 * can see at a glance how much of the product a regional language covers and
 * how much still falls back to English. This is a *report*, not a strict gate —
 * a pilot locale is allowed to be a subset (parity.test.ts already enforces the
 * subset is valid). It does assert a small floor so coverage can't silently
 * regress below the anonymous-journey baseline that shipped in LA-9b.
 *
 * `complete` locales are covered by the exact-parity assertions in
 * parity.test.ts and are skipped here.
 */

const TOTAL_KEYS = Object.keys(en).length;

// Floors per pilot locale: the minimum key count that must stay covered. Raise
// as a locale graduates surfaces; never let it drop. Marathi (mr) is the launch
// pilot — the student loop the video films (switcher, auth, dashboard,
// assignments, streaks, offline/sync). The floor is set a little under the
// shipped subset so a stray deletion trips it without churning on every add.
const PILOT_FLOORS: Partial<Record<Locale, number>> = { mr: 60 };

const counts: Partial<Record<Locale, number>> = {};

// Typed against the broad `LocaleMeta` union so the `'pilot'` comparison stays
// valid even when every currently-registered locale is `complete` (TS would
// otherwise narrow `coverage` to `'complete'` and flag the check as impossible).
const isPilot = (meta: LocaleMeta): boolean => meta.coverage === 'pilot';

beforeAll(async () => {
  for (const meta of LOCALES) {
    if (!isPilot(meta)) continue;
    const load = localeLoaders[meta.code];
    const module = (await load!()) as Record<string, Record<string, string> | undefined>;
    const dict = module[meta.code] ?? (module.default as Record<string, string> | undefined);
    counts[meta.code] = Object.keys(dict ?? {}).length;
  }
});

describe('pilot locale coverage report', () => {
  it('reports coverage for each pilot locale', () => {
    const pilots = LOCALES.filter(isPilot);
    for (const meta of pilots) {
      const n = counts[meta.code] ?? 0;
      const pct = ((n / TOTAL_KEYS) * 100).toFixed(1);
      console.log(`[i18n coverage] ${meta.code} (${meta.nativeName}): ${n}/${TOTAL_KEYS} keys (${pct}%)`);
      expect(n, `pilot locale ${meta.code} should define at least one key`).toBeGreaterThan(0);
    }
  });

  it('holds each pilot locale at or above its coverage floor', () => {
    for (const [code, floor] of Object.entries(PILOT_FLOORS) as [Locale, number][]) {
      const n = counts[code] ?? 0;
      expect(
        n,
        `${code} coverage ${n} dropped below its floor ${floor} — translations regressed`,
      ).toBeGreaterThanOrEqual(floor);
    }
  });
});
