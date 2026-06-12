import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
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
  /**
   * The authenticated user's durable `preferred_language`. Seeds the locale
   * when (and only when) there is no explicit device override in
   * localStorage — the precedence contract: device choice > profile > 'en'.
   */
  profileLocale?: Locale;
  /**
   * Fired on explicit locale changes (the switcher), not on seeding. The app
   * shell uses it to PATCH the profile so the choice travels across devices.
   */
  onLocaleChange?: (locale: Locale) => void;
}

export const I18nProvider = ({
  children,
  initialLocale,
  profileLocale,
  onLocaleChange,
}: I18nProviderProps) => {
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale ?? resolveInitialLocale());
  const [hiDict, setHiDict] = useState<LocaleDict | null>(hiDictCache);

  // Ref so setLocale stays referentially stable across handler re-creations.
  const onLocaleChangeRef = useRef(onLocaleChange);
  useEffect(() => {
    onLocaleChangeRef.current = onLocaleChange;
  });

  // Seed from the profile preference when the user has not made an explicit
  // choice on this device (adjust state during render —
  // react.dev/learn/you-might-not-need-an-effect).
  const [seededProfileLocale, setSeededProfileLocale] = useState<Locale | undefined>(undefined);
  if (profileLocale && profileLocale !== seededProfileLocale) {
    setSeededProfileLocale(profileLocale);
    let hasDeviceOverride = false;
    try {
      hasDeviceOverride = localStorage.getItem(LOCALE_STORAGE_KEY) !== null;
    } catch {
      hasDeviceOverride = true; // can't tell — don't override the session
    }
    if (!hasDeviceOverride) setLocaleState(profileLocale);
  }

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
    onLocaleChangeRef.current?.(next);
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
