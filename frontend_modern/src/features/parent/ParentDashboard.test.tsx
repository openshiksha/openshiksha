import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { I18nProvider, type Locale } from '@/shared/i18n';
import { UserRole } from '@/types/index';
import { ParentDashboard } from './ParentDashboard';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: mockGet,
  },
}));

const CHILD = {
  id: 5,
  username: 'asha',
  email: '',
  first_name: 'Asha',
  last_name: 'Verma',
  role: UserRole.STUDENT,
  grade: 8,
};

const PROFICIENCY = {
  id: 1,
  tag_name: 'Polynomials',
  subject_name: 'Mathematics',
  classroom_display: 'Class 8A',
  score: 0.72,
  tick_count: 12,
};

function mockEndpoints() {
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/users/me/children/')) return Promise.resolve({ data: [CHILD] });
    if (url.includes('proficiency')) return Promise.resolve({ data: { results: [PROFICIENCY] } });
    if (url.includes('assignments')) return Promise.resolve({ data: [] });
    return Promise.resolve({ data: [] });
  });
}

function renderDashboard(locale: Locale = 'en') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nProvider initialLocale={locale}>
        <MemoryRouter>
          <ParentDashboard />
        </MemoryRouter>
      </I18nProvider>
    </QueryClientProvider>,
  );
}

describe('ParentDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders the dashboard chrome in English by default', async () => {
    mockEndpoints();
    renderDashboard();

    await waitFor(() => expect(screen.getByText('Parent Dashboard')).toBeDefined());
    expect(screen.getByText("Asha's Overview")).toBeDefined();
    expect(screen.getByRole('button', { name: 'Progress' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'Assignments' })).toBeDefined();
  });

  it('renders the dashboard chrome in Hindi when the locale is hi', async () => {
    mockEndpoints();
    renderDashboard('hi');

    // Hindi dictionary loads via dynamic import — wait for the swap.
    await waitFor(() => expect(screen.getByText('अभिभावक डैशबोर्ड')).toBeDefined());
    expect(screen.getByText('Asha की प्रगति-झलक')).toBeDefined();
    expect(screen.getByRole('button', { name: 'प्रगति' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'असाइनमेंट' })).toBeDefined();
    // Authored/server content (subject, chapter tag) stays as authored.
    await waitFor(() => expect(screen.getByText('Mathematics')).toBeDefined());
    expect(screen.getByText('Polynomials')).toBeDefined();
  });
});
