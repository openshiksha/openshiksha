import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { en, type LocaleKey, type LocaleDict } from './locales/en';
import {
  I18nContext,
  interpolate,
  resolveInitialLocale,
  LOCALE_STORAGE_KEY,
  type Locale,
  type Translate,
} from './i18nContext';

// Module-level cache: after the first dynamic import, locale switches are
// synchronous for the rest of the session.
let hiDictCache: LocaleDict | null = null;

interface I18nProviderProps {
  children: ReactNode;
  /** Test/storybook override; production resolves from localStorage. */
  initialLocale?: Locale;
}

export const I18nProvider = ({ children, initialLocale }: I18nProviderProps) => {
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale ?? resolveInitialLocale());
  const [hiDict, setHiDict] = useState<LocaleDict | null>(hiDictCache);

  // Fetch the Hindi dictionary on demand (keeps it out of the entry chunk).
  // Until it arrives, t() serves the English fallback — never a blank
  // (initiative principle 3).
  useEffect(() => {
    if (locale !== 'hi' || hiDict) return;
    let cancelled = false;
    void import('./locales/hi').then((module) => {
      hiDictCache = module.hi;
      if (!cancelled) setHiDict(module.hi);
    });
    return () => {
      cancelled = true;
    };
  }, [locale, hiDict]);

  // Keep <html lang> in sync — screen readers and the Devanagari font stack
  // both key off it.
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    try {
      localStorage.setItem(LOCALE_STORAGE_KEY, next);
    } catch {
      // Storage unavailable — the choice still applies for this session.
    }
  }, []);

  const t = useCallback<Translate>(
    (key, vars) => {
      // Partial view: key parity is tsc-enforced, but the runtime fallback
      // stays honest if a locale file ever drifts (e.g. hand-edited build).
      const active: Partial<Record<LocaleKey, string>> =
        locale === 'hi' && hiDict ? hiDict : en;
      const template = active[key];
      if (template === undefined) {
        if (import.meta.env.DEV) {
          console.warn(`[i18n] missing "${key}" in locale "${locale}" — falling back to en`);
        }
        return interpolate(en[key], vars);
      }
      return interpolate(template, vars);
    },
    [locale, hiDict],
  );

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
};
