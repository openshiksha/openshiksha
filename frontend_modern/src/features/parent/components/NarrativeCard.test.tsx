import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { NarrativeCard } from './NarrativeCard';
import type { ParentProgressSummary } from '../useParentSummary';

const SUMMARY: ParentProgressSummary = {
  id: 1,
  parent: 10,
  child: 20,
  child_username: 'asha',
  child_name: 'Asha',
  week_start: '2026-06-01',
  week_end: '2026-06-07',
  summary_text: 'Asha practised on five days this week and is gaining confidence in fractions.',
  language: 'en',
  ticks_recorded: 42,
  active_days: 5,
  avg_score: 0.78,
  score_delta: 0.05,
  weak_chapters: [],
  strong_chapters: [],
  home_activities: [],
  alerts: [],
  has_urgent_alert: false,
  model_used: 'claude-sonnet-4-6',
  generated_at: '2026-06-07T10:00:00Z',
};

describe('NarrativeCard', () => {
  it('labels a real LLM summary as AI-generated', () => {
    render(<NarrativeCard summary={SUMMARY} />);

    expect(screen.getByText(/gaining confidence in fractions/)).toBeDefined();
    expect(screen.getByText('✨ AI-generated')).toBeDefined();
    expect(screen.queryByText(/AI was unavailable/)).toBeNull();
  });

  it('marks a stub fallback as an auto-summary rather than AI output', () => {
    render(<NarrativeCard summary={{ ...SUMMARY, model_used: 'stub' }} />);

    expect(screen.getByText('Auto-summary')).toBeDefined();
    expect(screen.getByText(/AI was unavailable/)).toBeDefined();
    expect(screen.queryByText('✨ AI-generated')).toBeNull();
  });
});
