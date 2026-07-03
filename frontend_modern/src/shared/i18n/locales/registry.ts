import type { LocaleDict } from './en';

/**
 * LA-9a — the locale registry: the single source of truth for "what locales
 * exist" and everything per-locale that used to be hardcoded across six files
 * (`i18nContext`, `I18nProvider`, `LanguageSwitcher`, `format`, `dateFnsLocale`,
 * the parity guard).
 *
 * The initiative North Star demands a third language be **a content task, not
 * an engineering task** (docs/initiatives/2026-language-access.md). Adding a
 * locale is now: append one `LOCALES` entry, widen the `Locale` union, register
 * a lazy `loader`, drop in a `locales/<code>.ts` dictionary. No consumer edits.
 *
 * Coverage model:
 * - `complete` ⇒ full key parity with English + no blanks (en, hi).
 * - `pilot`    ⇒ a *subset* is allowed; English fills the gaps at runtime
 *               (principle 3 — English is the fallback, never a blank). A new
 *               regional language can ship surface-by-surface this way.
 */

/**
 * Every supported UI locale. A string-literal union (not derived from the
 * array) so `t()` keys and locale params stay statically checked; the
 * `satisfies` below keeps the union and the registry honest about each other.
 */
export type Locale = 'en' | 'hi' | 'mr';

export interface LocaleMeta {
  /** Registry key — matches a `locales/<code>.ts` module. */
  code: Locale;
  /** Compact switcher glyph, e.g. 'EN', 'हिं'. */
  label: string;
  /** Endonym for aria-labels / a11y, e.g. 'English', 'हिंदी'. */
  nativeName: string;
  /** `document.documentElement.lang` value (font stack + screen readers). */
  htmlLang: string;
  /** BCP-47 tag for `Intl` (dates/numbers) and date-fns mapping. */
  intlLocale: string;
  /** `complete` ⇒ full parity required; `pilot` ⇒ subset allowed. */
  coverage: 'complete' | 'pilot';
}

/**
 * Lazy dictionary loaders. English is bundled eagerly (it's the default and the
 * fallback) so it is intentionally absent here; every other locale ships in its
 * own chunk fetched on first switch. An explicit map — rather than a template
 * `import(`./locales/${code}`)` — keeps Vite's static chunk analysis reliable
 * and the entry chunk untouched.
 */
export const localeLoaders: Partial<
  Record<Locale, () => Promise<{ default?: LocaleDict } & Record<string, unknown>>>
> = {
  hi: () => import('./hi'),
  mr: () => import('./mr'),
};

export const LOCALES = [
  {
    code: 'en',
    label: 'EN',
    nativeName: 'English',
    htmlLang: 'en',
    intlLocale: 'en-IN',
    coverage: 'complete',
  },
  {
    code: 'hi',
    label: 'हिं',
    nativeName: 'हिंदी',
    htmlLang: 'hi',
    intlLocale: 'hi-IN',
    coverage: 'complete',
  },
  {
    code: 'mr',
    label: 'मरा',
    nativeName: 'मराठी',
    htmlLang: 'mr',
    intlLocale: 'mr-IN',
    coverage: 'pilot',
  },
] as const satisfies readonly LocaleMeta[];

/** Default + fallback locale. */
export const DEFAULT_LOCALE: Locale = 'en';

const byCode = new Map<Locale, LocaleMeta>(LOCALES.map((l) => [l.code, l]));

/** Registry lookup. Falls back to English metadata for an unknown code. */
export const localeMeta = (code: Locale): LocaleMeta =>
  byCode.get(code) ?? byCode.get(DEFAULT_LOCALE)!;

/** Type guard used by `resolveInitialLocale` and the switcher. */
export const isLocale = (value: unknown): value is Locale =>
  typeof value === 'string' && byCode.has(value as Locale);
