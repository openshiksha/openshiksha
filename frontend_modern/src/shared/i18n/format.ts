import { useI18n, type Locale } from './i18nContext';
import { localeMeta } from './locales/registry';

/**
 * LA-8 — locale-aware date/number formatting via the platform `Intl` API.
 *
 * One shared helper so every surface formats absolute dates and counts the same
 * way for the active locale, instead of each screen reinventing
 * `toLocaleDateString`. `Intl` is built into the browser, so this adds nothing
 * to the entry chunk (principle 2 — no dependency for what the platform gives
 * us free). For *relative* dates ("3 दिन में") keep using the date-fns `hi`
 * locale wired up in LA-3 — this helper is for absolute dates and numbers.
 *
 * See docs/initiatives/2026-language-access.md.
 */

const intlLocale = (locale: Locale): string => localeMeta(locale).intlLocale;

/** Indian convention: "27 May 2026" / "27 मई 2026" (day-first, no comma). */
const DEFAULT_DATE_OPTS: Intl.DateTimeFormatOptions = {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
};

/**
 * Format an absolute date for the active locale.
 *
 * Defaults to a medium day-first style ("27 May 2026" / "27 मई 2026"); pass
 * `opts` to override. Invalid input is returned verbatim instead of throwing,
 * so a malformed API timestamp degrades to the raw string rather than crashing
 * a render.
 */
export const formatDate = (
  value: string | number | Date,
  locale: Locale,
  opts: Intl.DateTimeFormatOptions = DEFAULT_DATE_OPTS,
): string => {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return new Intl.DateTimeFormat(intlLocale(locale), opts).format(d);
};

/**
 * Format a number for the active locale.
 *
 * `en-IN`/`hi-IN` give Indian digit grouping (1,00,000) but keep **Latin
 * numerals** for both locales — a deliberate product decision for K-12 counts.
 * Do NOT "fix" this to Devanagari digits; Hindi-medium teachers and students
 * read scores and counts in Latin numerals.
 */
export const formatNumber = (
  value: number,
  locale: Locale,
  opts?: Intl.NumberFormatOptions,
): string => {
  if (!Number.isFinite(value)) return String(value);
  return new Intl.NumberFormat(intlLocale(locale), opts).format(value);
};

export interface BoundFormat {
  formatDate: (value: string | number | Date, opts?: Intl.DateTimeFormatOptions) => string;
  formatNumber: (value: number, opts?: Intl.NumberFormatOptions) => string;
}

/**
 * Hook returning `formatDate`/`formatNumber` already bound to the active locale,
 * mirroring `useT()`:
 *
 *   const { formatDate } = useFormat();
 *   <span>{formatDate(assignment.due_date)}</span>
 */
export const useFormat = (): BoundFormat => {
  const { locale } = useI18n();
  return {
    formatDate: (value, opts) => formatDate(value, locale, opts),
    formatNumber: (value, opts) => formatNumber(value, locale, opts),
  };
};
