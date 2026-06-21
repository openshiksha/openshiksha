import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { UserRole } from '@/types/index';
import { I18nProvider } from '@/shared/i18n';
import { ProfilePage } from './ProfilePage';

const mockUser = {
  id: 1,
  username: 'student1',
  email: 'student@test.com',
  first_name: 'Asha',
  last_name: 'Verma',
  role: UserRole.STUDENT,
  phone_number: '',
  email_reminders_opt_out: false,
  preferred_language: 'en' as const,
};

vi.mock('@/shared/hooks/useAuth', () => ({
  useAuth: () => ({ user: mockUser, isAuthenticated: true, isLoading: false }),
}));

vi.mock('@/api/auth', () => ({
  authApi: {
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));

function renderProfilePage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nProvider initialLocale="en">
        <ProfilePage />
      </I18nProvider>
    </QueryClientProvider>,
  );
}

describe('ProfilePage — language preference (LA-2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders the language selector seeded from the user profile', () => {
    renderProfilePage();
    const select = screen.getByLabelText(/language/i) as HTMLSelectElement;
    expect(select.value).toBe('en');
    expect(screen.getByRole('option', { name: 'English' })).toBeDefined();
    expect(screen.getByRole('option', { name: /हिंदी/ })).toBeDefined();
  });

  it('includes preferred_language in the save payload', async () => {
    const { authApi } = await import('@/api/auth');
    vi.mocked(authApi.updateProfile).mockResolvedValueOnce({
      ...mockUser,
      preferred_language: 'hi',
    });

    renderProfilePage();
    fireEvent.change(screen.getByLabelText(/language/i), { target: { value: 'hi' } });
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(authApi.updateProfile).toHaveBeenCalled();
    });
    expect(vi.mocked(authApi.updateProfile).mock.calls[0][0]).toEqual(
      expect.objectContaining({ preferred_language: 'hi' }),
    );
  });

  it('applies the saved language to the live UI (localStorage persisted)', async () => {
    const { authApi } = await import('@/api/auth');
    vi.mocked(authApi.updateProfile).mockResolvedValueOnce({
      ...mockUser,
      preferred_language: 'hi',
    });

    renderProfilePage();
    fireEvent.change(screen.getByLabelText(/language/i), { target: { value: 'hi' } });
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(localStorage.getItem('os_lang')).toBe('hi');
    });
    expect(document.documentElement.lang).toBe('hi');
  });
});
