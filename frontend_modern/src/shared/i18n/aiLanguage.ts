import { type Locale } from './i18nContext';

/**
 * Languages the LLM/email layer can currently *generate* content in. This is a
 * narrower set than the UI `Locale` union: a pilot/regional locale (e.g. 'mr',
 * LA-9) has translated UI chrome but no authored LLM prompt yet.
 */
export type AiLanguage = 'en' | 'hi';

const AI_SUPPORTED: readonly Locale[] = ['en', 'hi'];

/**
 * Map a UI locale to a supported AI-generation language. Unsupported locales
 * fall back to English so an explanation/summary request never carries a
 * language the prompt can't honor — principle 1 (authored/AI content is a
 * separate track from UI chrome). The backend enforces the same fallback so a
 * direct API call is safe too (LA-9d).
 */
export const toAiLanguage = (locale: Locale): AiLanguage =>
  AI_SUPPORTED.includes(locale) ? (locale as AiLanguage) : 'en';
