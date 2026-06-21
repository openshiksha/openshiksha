import { createContext, useContext } from 'react';
import { en, type LocaleKey } from './locales/en';
import { DEFAULT_LOCALE, isLocale, type Locale } from './locales/registry';

/**
 * OpenShiksha i18n — a deliberately tiny in-house module (no i18next).
 *
 * The set of locales lives in `locales/registry.ts` (LA-9a): one entry per
 * language drives the switcher, `Intl` formatting, the dict loader, and the
 * parity guard, so a new language is a content task, not an engineering one
 * (docs/initiatives/2026-language-access.md, North Star). An in-house module is
 * still the right call against a 160 kB entry-chunk budget (principle 2):
 * English is bundled eagerly (default + fallback); every other locale is
 * fetched with a dynamic import on first switch, so the entry chunk doesn't
 * grow with the language count.
 */

export type { Locale };
export { isLocale };

/** localStorage key for the per-device language override. */
export const LOCALE_STORAGE_KEY = 'os_lang';

/**
 * Precedence contract for the boot locale (LA-2 adds the profile layer):
 * explicit device choice (localStorage) > profile `preferred_language` > 'en'.
 */
export const resolveInitialLocale = (): Locale => {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (isLocale(stored)) return stored;
  } catch {
    // Storage unavailable (private mode, SSR) — fall through to default.
  }
  return DEFAULT_LOCALE;
};

export type TranslateVars = Record<string, string | number>;
export type Translate = (key: LocaleKey, vars?: TranslateVars) => string;

export interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Translate;
}

export const interpolate = (template: string, vars?: TranslateVars): string => {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in vars ? String(vars[name]) : match,
  );
};

// Without a provider (isolated component tests, storybook) the context
// degrades to a working English-only translator instead of throwing —
// principle 3: English is the fallback, never a blank.
const defaultI18nValue: I18nContextValue = {
  locale: DEFAULT_LOCALE,
  setLocale: () => {
    if (import.meta.env.DEV) {
      console.warn('[i18n] setLocale called outside <I18nProvider> — ignored');
    }
  },
  t: (key, vars) => interpolate(en[key], vars),
};

export const I18nContext = createContext<I18nContextValue | null>(null);

export const useI18n = (): I18nContextValue => useContext(I18nContext) ?? defaultI18nValue;
