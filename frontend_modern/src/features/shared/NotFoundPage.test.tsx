import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { NotFoundPage } from './NotFoundPage';

describe('<NotFoundPage />', () => {
  it('renders 404, headline and back-home link', () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    );
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText(/Nothing behind this door/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Back to home/i });
    expect(link).toHaveAttribute('href', '/');
  });
});
