import { hi as hiDateLocale } from 'date-fns/locale';
import type { Locale as DateFnsLocale } from 'date-fns';
import type { Locale } from './i18nContext';

/**
 * date-fns locale for relative-time strings ("3 दिन में" instead of
 * "in 3 days"). `undefined` keeps date-fns's built-in English default, used
 * for English and for any locale without a date-fns mapping (it still gets
 * localized chrome + `Intl` absolute dates — only relative phrasing falls back).
 *
 * One entry per locale that has a date-fns locale (LA-9a registry model):
 * append a line as each language lands its student-loop chrome (mr in LA-9c).
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
