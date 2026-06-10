import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { RecommendationsPanel } from './RecommendationsPanel';
import type { ContentRecommendation } from './useRecommendations';
import type { PracticePlan } from './usePracticePlan';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: mockGet,
  },
}));

const REC: ContentRecommendation = {
  id: 11,
  chapter: 4,
  chapter_name: 'Fractions',
  subject_name: 'Mathematics',
  subject_room: 1,
  problem_set: null,
  reason: 'low_score',
  reason_display: 'Recent scores were low in this chapter',
  priority: 1,
  priority_display: 'Urgent',
  score_snapshot: 0.42,
  is_actioned: false,
  is_active: true,
  generated_at: '2026-06-09T08:00:00Z',
  actioned_at: null,
};

const PLAN: PracticePlan = {
  id: 5,
  subject_room: 1,
  plan_date: '2026-06-09',
  estimated_minutes: 20,
  is_completed: false,
  recommendations: [REC],
  generated_at: '2026-06-09T08:00:00Z',
};

/** Routes mockGet by URL: recommendations list + today's practice plan. */
function mockEndpoints({
  recommendations,
  plan,
  failRecommendations = false,
}: {
  recommendations: ContentRecommendation[];
  plan: PracticePlan | null;
  failRecommendations?: boolean;
}) {
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/ai/recommendations/')) {
      if (failRecommendations) return Promise.reject(new Error('boom'));
      return Promise.resolve({ data: { results: recommendations } });
    }
    if (url.startsWith('/ai/practice-plans/')) {
      if (plan === null) return Promise.reject({ response: { status: 404 } });
      return Promise.resolve({ data: plan });
    }
    return Promise.reject(new Error(`unexpected GET ${url}`));
  });
}

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <RecommendationsPanel />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('RecommendationsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows a skeleton while recommendations load instead of popping in', async () => {
    mockEndpoints({ recommendations: [REC], plan: PLAN });
    renderPanel();

    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);

    await waitFor(() => expect(screen.getByText('Fractions')).toBeDefined());
  });

  it('renders recommendations with a priority badge and the student score', async () => {
    mockEndpoints({ recommendations: [REC], plan: PLAN });
    renderPanel();

    await waitFor(() => expect(screen.getByText('Fractions')).toBeDefined());
    expect(screen.getByText('URGENT')).toBeDefined();
    expect(screen.getByText('Recent scores were low in this chapter')).toBeDefined();
    expect(screen.getByText('42%')).toBeDefined();
    expect(screen.getByText('your score')).toBeDefined();
    expect(screen.getByText(/~20 min/)).toBeDefined();
  });

  it('explains what unlocks recommendations when there are none yet', async () => {
    mockEndpoints({ recommendations: [], plan: null });
    renderPanel();

    await waitFor(() =>
      expect(screen.getByText(/answer a few assignment questions/i)).toBeDefined()
    );
    expect(screen.getByText('What to Practice Next')).toBeDefined();
  });

  it('hides the panel entirely when the fetch fails', async () => {
    mockEndpoints({ recommendations: [], plan: null, failRecommendations: true });
    const { container } = renderPanel();

    await waitFor(() => expect(mockGet).toHaveBeenCalled());
    await waitFor(() => expect(container.firstChild).toBeNull());
  });
});
