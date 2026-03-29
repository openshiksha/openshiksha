import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { LoginPage } from './LoginPage';

// Mock authApi
vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    verifyToken: vi.fn().mockResolvedValue(false),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function renderLoginPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders username and password fields', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/username/i)).toBeDefined();
    expect(screen.getByLabelText(/password/i)).toBeDefined();
  });

  it('renders the sign in button', () => {
    renderLoginPage();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDefined();
  });

  it('disables submit button when fields are empty', () => {
    renderLoginPage();
    const button = screen.getByRole('button', { name: /sign in/i });
    expect(button).toHaveAttribute('disabled');
  });

  it('enables submit button when both fields are filled', async () => {
    renderLoginPage();
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'student1' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'pass123' } });
    const button = screen.getByRole('button', { name: /sign in/i });
    expect(button).not.toHaveAttribute('disabled');
  });

  it('shows error message on failed login', async () => {
    const { authApi } = await import('@/api/auth');
    vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Invalid credentials'));

    renderLoginPage();
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'wrong' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form')!);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeDefined();
      expect(screen.getByText(/invalid username or password/i)).toBeDefined();
    });
  });
});
