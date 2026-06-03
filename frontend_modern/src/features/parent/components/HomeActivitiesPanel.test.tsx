import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { HomeActivitiesPanel } from './HomeActivitiesPanel';
import type { HomeActivity } from '../useParentSummary';

describe('HomeActivitiesPanel', () => {
  it('renders nothing when activities are empty', () => {
    const { container } = render(<HomeActivitiesPanel activities={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders title, description, and chapter name per activity', () => {
    const activities: HomeActivity[] = [
      {
        title: 'Practice long division',
        description: '15 minutes together on long division worksheets.',
        chapter_name: 'Division',
      },
    ];
    render(<HomeActivitiesPanel activities={activities} />);
    expect(screen.getByText('Practice long division')).toBeDefined();
    expect(screen.getByText('15 minutes together on long division worksheets.')).toBeDefined();
    expect(screen.getByText('Division')).toBeDefined();
  });

  it('marks celebratory activities with data-celebrate', () => {
    const activities: HomeActivity[] = [
      { title: 'Great work this week!', description: 'Keep up the streak.', chapter_name: 'Algebra' },
    ];
    render(<HomeActivitiesPanel activities={activities} />);
    const card = document.querySelector('[data-celebrate]');
    expect(card).not.toBeNull();
  });
});
