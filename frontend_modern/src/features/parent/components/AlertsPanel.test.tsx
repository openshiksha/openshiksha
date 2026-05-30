import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AlertsPanel } from './AlertsPanel';
import type { ParentAlert } from '../useParentSummary';

describe('AlertsPanel', () => {
  it('renders nothing when alerts array is empty', () => {
    const { container } = render(<AlertsPanel alerts={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders one card per alert with severity attribute', () => {
    const alerts: ParentAlert[] = [
      { severity: 'urgent', label: 'No practice in 10 days', detail: 'Aanya has not opened a question in 10 days.' },
      { severity: 'attention', label: 'Score dropped 15%', detail: 'Average score fell from 78% to 63%.' },
      { severity: 'info', label: 'New chapter unlocked', detail: 'Polynomials is now available.' },
    ];
    render(<AlertsPanel alerts={alerts} />);
    expect(screen.getByText('No practice in 10 days')).toBeDefined();
    expect(screen.getByText('Score dropped 15%')).toBeDefined();
    expect(screen.getByText('New chapter unlocked')).toBeDefined();

    const cards = document.querySelectorAll('[data-severity]');
    expect(cards.length).toBe(3);
    expect(cards[0].getAttribute('data-severity')).toBe('urgent');
    expect(cards[1].getAttribute('data-severity')).toBe('attention');
    expect(cards[2].getAttribute('data-severity')).toBe('info');
  });
});
