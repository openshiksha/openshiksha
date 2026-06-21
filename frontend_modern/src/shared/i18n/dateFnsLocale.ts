import { hi as hiDateLocale } from 'date-fns/locale';
import type { Locale as DateFnsLocale } from 'date-fns';
import type { Locale } from './i18nContext';

/**
 * date-fns locale for relative-time strings ("3 दिन में" instead of
 * "in 3 days"). `undefined` keeps date-fns's built-in English default, used
 * for English and for any locale without a date-fns mapping (it still gets
 * localized chrome + `Intl` absolute dates — only relative phrasing falls back).
 *
 * One entry per locale that has a date-fns locale (LA-9a registry model).
 * Marathi (mr) is intentionally absent — date-fns 4.x ships no `mr` locale, so
 * mr relative dates fall back to English phrasing while mr absolute dates still
 * localize via the `Intl` `mr-IN` formatter (format.ts). Add a line here if a
 * future date-fns version (or a custom locale) provides Marathi.
 *
 * Deliberately NOT re-exported from the i18n barrel: the barrel is imported by
 * App (the entry chunk) and these date locales should only ship inside the lazy
 * page chunks that format relative dates. Import this module directly.
 */
const DATE_FNS_LOCALES: Partial<Record<Locale, DateFnsLocale>> = {
  hi: hiDateLocale,
};

export const dateFnsLocaleFor = (locale: Locale): DateFnsLocale | undefined =>
  DATE_FNS_LOCALES[locale];
