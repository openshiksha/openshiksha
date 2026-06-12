import { createContext, useContext } from 'react';
import { en, type LocaleKey } from './locales/en';

/**
 * OpenShiksha i18n — a deliberately tiny in-house module (no i18next).
 *
 * Two locales with `{var}` interpolation don't justify a 45 kB dependency
 * against a 160 kB entry-chunk budget; see
 * docs/initiatives/2026-language-access.md, principle 2. English is bundled
 * eagerly (it's the fallback and the default); Hindi is fetched with a
 * dynamic import the first time the user switches, so the entry chunk does
 * not grow.
 */

export type Locale = 'en' | 'hi';

/** localStorage key for the per-device language override. */
export const LOCALE_STORAGE_KEY = 'os_lang';

export const isLocale = (value: unknown): value is Locale => value === 'en' || value === 'hi';

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
  return 'en';
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
  locale: 'en',
  setLocale: () => {
    if (import.meta.env.DEV) {
      console.warn('[i18n] setLocale called outside <I18nProvider> — ignored');
    }
  },
  t: (key, vars) => interpolate(en[key], vars),
};

export const I18nContext = createContext<I18nContextValue | null>(null);

export const useI18n = (): I18nContextValue => useContext(I18nContext) ?? defaultI18nValue;
