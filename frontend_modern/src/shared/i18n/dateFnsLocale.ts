import { hi as hiDateLocale } from 'date-fns/locale';
import type { Locale as DateFnsLocale } from 'date-fns';
import type { Locale } from './i18nContext';

/**
 * date-fns locale for relative-time strings ("3 दिन में" instead of
 * "in 3 days") when the UI is in Hindi. `undefined` keeps date-fns's
 * built-in English default.
 *
 * Deliberately NOT re-exported from the i18n barrel: the barrel is imported
 * by App (the entry chunk) and the Hindi date locale should only ship inside
 * the lazy page chunks that format dates. Import this module directly.
 */
export const dateFnsLocaleFor = (locale: Locale): DateFnsLocale | undefined =>
  locale === 'hi' ? hiDateLocale : undefined;
