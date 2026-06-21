/**
 * Pure helpers shared by question pickers and preview panels.
 * Kept in a separate file from React components so Vite/fast-refresh's
 * "component-only exports" rule stays happy.
 */
import type { LocaleKey, Translate } from '@/shared/i18n';

const TYPE_LABEL: Record<string, string> = {
  mcq: 'MCQ',
  numeric: 'Numeric',
  fill_blank: 'Fill blank',
  multi_select: 'Multi-select',
  matching: 'Matching',
  compound: 'Compound',
};

const TYPE_TONE: Record<string, 'brand' | 'neutral' | 'success' | 'attention' | 'urgent'> = {
  mcq: 'brand',
  multi_select: 'attention',
  numeric: 'success',
  fill_blank: 'neutral',
  matching: 'neutral',
  compound: 'urgent',
};

export const typeLabel = (t: string) => TYPE_LABEL[t] ?? t.replace('_', ' ');
export const typeTone = (t: string) => TYPE_TONE[t] ?? 'neutral';

const TYPE_KEY: Record<string, LocaleKey> = {
  mcq: 'qtype.mcq',
  numeric: 'qtype.numeric',
  fill_blank: 'qtype.fill_blank',
  multi_select: 'qtype.multi_select',
  matching: 'qtype.matching',
  compound: 'qtype.compound',
};

/** Locale-aware question-type label. Falls back to the raw type for unknowns. */
export const localizedTypeLabel = (translate: Translate, type: string): string => {
  const key = TYPE_KEY[type];
  return key ? translate(key) : type.replace('_', ' ');
};
export const difficultyStars = (d: number) =>
  '★'.repeat(d) + '☆'.repeat(Math.max(0, 5 - d));
