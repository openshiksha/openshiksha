import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { en, type LocaleKey } from './locales/en';
import { localeLoaders, localeMeta, DEFAULT_LOCALE } from './locales/registry';
import {
  I18nContext,
  interpolate,
  resolveInitialLocale,
  LOCALE_STORAGE_KEY,
  type Locale,
  type Translate,
} from './i18nContext';

/**
 * A loaded locale dictionary may be a complete (`hi`) or a pilot subset (`mr`)
 * of the English key set — English fills any gaps in `t()`.
 */
type LoadedDict = Partial<Record<LocaleKey, string>>;

// Module-level cache keyed by locale: after the first dynamic import, switching
// back to a locale is synchronous for the rest of the session. English is the
// eager fallback and never goes through the loader, so it's absent here.
const dictCache = new Map<Locale, LoadedDict>();

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
  // Loaded non-English dictionaries this session. Seeded from the module cache
  // so a re-mount doesn't re-fetch; only ever grown asynchronously (after a
  // dynamic import resolves), never mutated synchronously inside an effect.
  const [loadedDicts, setLoadedDicts] = useState<Map<Locale, LoadedDict>>(
    () => new Map(dictCache),
  );

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

  // Fetch the active locale's dictionary on demand (keeps every non-English
  // locale out of the entry chunk). English needs no fetch; until a fetched
  // dict arrives, t() serves the English fallback — never a blank (principle 3).
  useEffect(() => {
    // English needs no fetch; an already-loaded dict is reused (no setState).
    if (locale === DEFAULT_LOCALE || loadedDicts.has(locale)) return;
    const load = localeLoaders[locale];
    if (!load) return; // No loader registered — stay on the English fallback.
    let cancelled = false;
    void load().then((module) => {
      // The dictionary is exported under the locale code (e.g. `hi`, `mr`).
      const dict = ((module as Record<string, LoadedDict | undefined>)[locale] ??
        (module.default as LoadedDict | undefined)) as LoadedDict | undefined;
      if (!dict) return;
      dictCache.set(locale, dict);
      if (cancelled) return;
      setLoadedDicts((prev) => new Map(prev).set(locale, dict));
    });
    return () => {
      cancelled = true;
    };
  }, [locale, loadedDicts]);

  // Keep <html lang> in sync — screen readers and the Devanagari font stack
  // both key off it. Use the registry's htmlLang so a locale can map to a
  // different document language tag than its registry code if needed.
  useEffect(() => {
    document.documentElement.lang = localeMeta(locale).htmlLang;
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
      // English (the default + fallback) is always the eager `en`. A non-English
      // locale uses its loaded dict if present, else the English fallback while
      // it streams in or for any key a pilot locale doesn't define (principle 3).
      const active: Partial<Record<LocaleKey, string>> =
        locale === DEFAULT_LOCALE ? en : (loadedDicts.get(locale) ?? en);
      const template = active[key];
      if (template === undefined) {
        if (import.meta.env.DEV) {
          console.warn(`[i18n] missing "${key}" in locale "${locale}" — falling back to en`);
        }
        return interpolate(en[key], vars);
      }
      return interpolate(template, vars);
    },
    [locale, loadedDicts],
  );

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
};
