import { describe, it, expect } from 'vitest';
import {
  LOCALES,
  localeMeta,
  isLocale,
  localeLoaders,
  DEFAULT_LOCALE,
} from './locales/registry';

/**
 * LA-9a — guards the locale registry, the single source of truth that the
 * switcher, dict loader, `Intl` formatting, and the parity guard all read from.
 * If these hold, adding a language is a content task (new entry + dictionary),
 * not an engineering one.
 */
describe('locale registry', () => {
  it('every entry has non-empty metadata fields', () => {
    for (const meta of LOCALES) {
      expect(meta.code, 'code').toBeTruthy();
      expect(meta.label.trim(), `label for ${meta.code}`).not.toBe('');
      expect(meta.nativeName.trim(), `nativeName for ${meta.code}`).not.toBe('');
      expect(meta.htmlLang.trim(), `htmlLang for ${meta.code}`).not.toBe('');
      expect(meta.intlLocale, `intlLocale for ${meta.code}`).toMatch(/^[a-z]{2}(-[A-Z]{2})?$/);
      expect(['complete', 'pilot']).toContain(meta.coverage);
    }
  });

  it('codes are unique', () => {
    const codes = LOCALES.map((l) => l.code);
    expect(new Set(codes).size).toBe(codes.length);
  });

  it('English is registered, the default, and complete', () => {
    expect(DEFAULT_LOCALE).toBe('en');
    const en = LOCALES.find((l) => l.code === 'en');
    expect(en).toBeDefined();
    expect(en!.coverage).toBe('complete');
  });

  it('localeMeta round-trips every registered code', () => {
    for (const meta of LOCALES) {
      expect(localeMeta(meta.code)).toEqual(meta);
    }
  });

  it('localeMeta falls back to the default for an unknown code', () => {
    // @ts-expect-error — exercising the runtime fallback with an invalid code.
    expect(localeMeta('zz').code).toBe(DEFAULT_LOCALE);
  });

  it('isLocale accepts registered codes and rejects everything else', () => {
    for (const meta of LOCALES) expect(isLocale(meta.code)).toBe(true);
    expect(isLocale('zz')).toBe(false);
    expect(isLocale(null)).toBe(false);
    expect(isLocale(42)).toBe(false);
  });

  it('English has no loader (eager) and every other locale does', () => {
    expect(localeLoaders.en).toBeUndefined();
    for (const meta of LOCALES) {
      if (meta.code === 'en') continue;
      expect(localeLoaders[meta.code], `loader for ${meta.code}`).toBeTypeOf('function');
    }
  });
});
