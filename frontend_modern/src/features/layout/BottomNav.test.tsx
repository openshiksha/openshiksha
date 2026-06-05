import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect } from 'vitest';
import { BottomNav } from './BottomNav';
import { UserRole } from '@/types/index';

const mockUseAuth = vi.fn();
vi.mock('@/shared/hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

const renderAt = (pathname: string) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[pathname]}>
        <BottomNav />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe('<BottomNav />', () => {
  it('renders nothing when the user is not signed in', () => {
    mockUseAuth.mockReturnValue({ user: undefined });
    const { container } = renderAt('/');
    expect(container.firstChild).toBeNull();
  });

  it('shows the four student tabs for a STUDENT', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: 'a', role: UserRole.STUDENT },
    });
    renderAt('/student');
    expect(screen.getByRole('link', { name: /Home/i })).toHaveAttribute('href', '/student');
    expect(screen.getByRole('link', { name: /Browse/i })).toHaveAttribute(
      'href',
      '/student/browse',
    );
    expect(screen.getByRole('link', { name: /Path/i })).toHaveAttribute(
      'href',
      '/student/learning-path',
    );
    expect(screen.getByRole('link', { name: /Profile/i })).toHaveAttribute('href', '/profile');
  });

  it('marks the matching tab as the current page (prefix match for Browse)', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: 'a', role: UserRole.STUDENT },
    });
    renderAt('/student/browse/chapter/42');
    const browse = screen.getByRole('link', { name: /Browse/i });
    expect(browse).toHaveAttribute('aria-current', 'page');
    const home = screen.getByRole('link', { name: /Home/i });
    expect(home).not.toHaveAttribute('aria-current');
  });

  it('shows the teacher set for a TEACHER', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: 't', role: UserRole.TEACHER },
    });
    renderAt('/teacher');
    expect(screen.getByRole('link', { name: /Questions/i })).toHaveAttribute(
      'href',
      '/teacher/questions',
    );
    expect(screen.queryByRole('link', { name: /Browse/i })).not.toBeInTheDocument();
  });

  it('treats OPEN_STUDENT the same as STUDENT', () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, username: 'o', role: UserRole.OPEN_STUDENT },
    });
    renderAt('/student');
    expect(screen.getByRole('link', { name: /Browse/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Path/i })).toBeInTheDocument();
  });
});
