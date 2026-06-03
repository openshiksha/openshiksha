import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SectionHeading } from './SectionHeading';

describe('<SectionHeading />', () => {
  it('renders title as h2 by default', () => {
    render(<SectionHeading title="Assignments due" />);
    const heading = screen.getByRole('heading', { name: 'Assignments due' });
    expect(heading.tagName).toBe('H2');
  });

  it('renders as h1 when `as` is set', () => {
    render(<SectionHeading title="Dashboard" as="h1" />);
    const heading = screen.getByRole('heading', { name: 'Dashboard' });
    expect(heading.tagName).toBe('H1');
  });

  it('renders eyebrow, description and action slot', () => {
    render(
      <SectionHeading
        eyebrow="Today"
        title="Practice"
        description="Pick something to work on"
        action={<a href="/all">View all</a>}
      />,
    );
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Pick something to work on')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View all' })).toBeInTheDocument();
  });
});
