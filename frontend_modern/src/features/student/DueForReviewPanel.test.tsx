import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { I18nProvider, type Locale } from '@/shared/i18n';
import { DueForReviewPanel } from './DueForReviewPanel';
import type { SRSEntry } from './useSpacedRepetitionDue';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: mockGet,
  },
}));

const today = new Date().toISOString().slice(0, 10);

const ENTRY: SRSEntry = {
  id: 7,
  knowledge_node: 3,
  chapter_name: 'Polynomials',
  interval_days: 6,
  easiness_factor: 2.5,
  repetitions: 2,
  next_review_date: today,
  last_reviewed_at: '2026-06-03T08:00:00Z',
};

const OVERDUE_ENTRY: SRSEntry = {
  ...ENTRY,
  id: 8,
  chapter_name: 'Fractions',
  next_review_date: '2020-01-01',
};

function mockDueEntries(entries: SRSEntry[] | Error) {
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/ai/spaced-repetition/due/')) {
      if (entries instanceof Error) return Promise.reject(entries);
      return Promise.resolve({ data: entries });
    }
    return Promise.reject(new Error(`unexpected GET ${url}`));
  });
}

function renderPanel(locale: Locale = 'en') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <I18nProvider initialLocale={locale}>
        <MemoryRouter>
          <DueForReviewPanel />
        </MemoryRouter>
      </I18nProvider>
    </QueryClientProvider>
  );
}

describe('DueForReviewPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows a skeleton while due entries load instead of popping in', async () => {
    mockDueEntries([ENTRY]);
    renderPanel();

    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
  });

  it('renders due entries with urgency labels and a practice link', async () => {
    mockDueEntries([ENTRY, OVERDUE_ENTRY]);
    renderPanel();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    expect(screen.getByText('Due today')).toBeDefined();
    expect(screen.getByText(/Overdue since 2020-01-01/)).toBeDefined();
    expect(screen.getByText('1 overdue')).toBeDefined();

    const links = screen.getAllByRole('link', { name: /practice/i });
    expect(links.length).toBe(2);
    // Overdue entries sort first.
    expect(links[0].getAttribute('href')).toBe('/student/srs-drill/8');
  });

  it('explains what unlocks the review schedule when nothing is due', async () => {
    mockDueEntries([]);
    renderPanel();

    await waitFor(() =>
      expect(screen.getByText(/finish a few assignments/i)).toBeDefined()
    );
    expect(screen.getByText('Due for Review')).toBeDefined();
  });

  it('renders the panel chrome in Hindi when the locale is hi', async () => {
    mockDueEntries([ENTRY]);
    renderPanel('hi');

    // Hindi dictionary loads via dynamic import — wait for the swap.
    await waitFor(() => expect(screen.getByText('दोहराव के लिए तैयार')).toBeDefined());
    expect(screen.getByText('आज करना है')).toBeDefined();
    expect(screen.getByRole('link', { name: 'अभ्यास' })).toBeDefined();
    // Authored content stays as authored (initiative principle 1).
    expect(screen.getByText('Polynomials')).toBeDefined();
  });

  it('hides the panel entirely when the fetch fails', async () => {
    mockDueEntries(new Error('boom'));
    const { container } = renderPanel();

    await waitFor(() => expect(mockGet).toHaveBeenCalled());
    await waitFor(() => expect(container.firstChild).toBeNull());
  });
});
