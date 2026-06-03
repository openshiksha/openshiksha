import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from './EmptyState';
import { Button } from './Button';

describe('<EmptyState />', () => {
  it('renders title and description', () => {
    render(<EmptyState title="No assignments yet" description="Check back soon." />);
    expect(screen.getByText('No assignments yet')).toBeInTheDocument();
    expect(screen.getByText('Check back soon.')).toBeInTheDocument();
  });

  it('renders an action slot when provided', () => {
    render(
      <EmptyState
        title="Empty"
        action={<Button>Browse practice</Button>}
      />,
    );
    expect(screen.getByRole('button', { name: 'Browse practice' })).toBeInTheDocument();
  });

  it('uses role=status for screen readers', () => {
    render(<EmptyState title="Empty" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
