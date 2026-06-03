import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Stat } from './Stat';

describe('<Stat />', () => {
  it('renders label and value', () => {
    render(<Stat label="Streak" value="14d" />);
    expect(screen.getByText('Streak')).toBeInTheDocument();
    expect(screen.getByText('14d')).toBeInTheDocument();
  });

  it('renders delta badge when provided', () => {
    render(<Stat label="Score" value="84%" delta="+6%" tone="success" />);
    expect(screen.getByText('+6%')).toBeInTheDocument();
  });

  it('renders optional hint text', () => {
    render(<Stat label="Due" value="3" hint="of 5 assignments" />);
    expect(screen.getByText('of 5 assignments')).toBeInTheDocument();
  });
});
