import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { CreateQuestionPage } from './CreateQuestionPage';

// The page is data-driven through React Query hooks that all read from the
// shared apiClient; stub it so the create-mode form renders without network.
const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));
vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet, post: vi.fn(), patch: vi.fn() },
}));

const renderPage = (locale: 'en' | 'hi' = 'en') => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <I18nProvider initialLocale={locale}>
        <MemoryRouter initialEntries={['/teacher/questions/new']}>
          <Routes>
            <Route path="/teacher/questions/new" element={<CreateQuestionPage />} />
          </Routes>
        </MemoryRouter>
      </I18nProvider>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  mockGet.mockReset();
  // Subject rooms + chapters both come back empty — enough to render the form.
  mockGet.mockResolvedValue({ data: [] });
});

describe('<CreateQuestionPage />', () => {
  it('renders the create-mode heading in English by default', () => {
    renderPage('en');
    expect(screen.getByRole('heading', { name: 'Create Question' })).toBeInTheDocument();
  });

  it('renders the create-mode heading in Hindi when the locale is हिं', async () => {
    renderPage('hi');
    // प्रश्न बनाएँ = "Create Question" per the Glossary register.
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'प्रश्न बनाएँ' })).toBeInTheDocument();
    });
  });
});
