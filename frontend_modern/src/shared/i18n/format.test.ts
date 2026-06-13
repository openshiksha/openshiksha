import { describe, it, expect } from 'vitest';
import { formatDate, formatNumber } from './format';

/**
 * LA-8 — locale-aware date/number helper. Asserts the medium day-first style,
 * an opts override, invalid-input passthrough, and Indian-grouping/Latin-digit
 * number formatting for both locales.
 */

describe('formatDate', () => {
  const may27 = '2026-05-27T10:00:00Z';

  it('formats a medium day-first date in English', () => {
    expect(formatDate(may27, 'en')).toBe('27 May 2026');
  });

  it('formats a medium day-first date in Hindi', () => {
    // Devanagari month name; day/year stay Latin numerals.
    expect(formatDate(may27, 'hi')).toBe('27 मई 2026');
  });

  it('honours an opts override', () => {
    expect(formatDate(may27, 'en', { month: 'long', year: 'numeric' })).toBe('May 2026');
  });

  it('returns invalid input verbatim instead of throwing', () => {
    expect(formatDate('not-a-date', 'en')).toBe('not-a-date');
    expect(formatDate('not-a-date', 'hi')).toBe('not-a-date');
  });

  it('accepts a Date instance', () => {
    expect(formatDate(new Date(may27), 'en')).toBe('27 May 2026');
  });
});

describe('formatNumber', () => {
  it('uses Indian grouping with Latin digits in English', () => {
    expect(formatNumber(100000, 'en')).toBe('1,00,000');
  });

  it('uses Indian grouping with Latin digits in Hindi (not Devanagari)', () => {
    expect(formatNumber(100000, 'hi')).toBe('1,00,000');
  });

  it('returns non-finite input verbatim', () => {
    expect(formatNumber(NaN, 'en')).toBe('NaN');
  });
});
