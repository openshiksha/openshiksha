/**
 * Pure helpers shared by question pickers and preview panels.
 * Kept in a separate file from React components so Vite/fast-refresh's
 * "component-only exports" rule stays happy.
 */

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
export const difficultyStars = (d: number) =>
  '★'.repeat(d) + '☆'.repeat(Math.max(0, 5 - d));
