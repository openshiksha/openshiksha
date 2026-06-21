import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { WeeklyReportPanel } from './WeeklyReportPanel';
import type { WeeklyClassReport } from './useWeeklyReport';

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
  },
}));

const REPORT: WeeklyClassReport = {
  id: 3,
  subject_room: 1,
  subject_name: 'Mathematics',
  classroom_label: 'Std 8 A',
  week_start: '2026-06-01',
  week_end: '2026-06-07',
  summary_text: 'The class practised steadily this week and is improving in algebra.',
  total_students: 30,
  active_students: 24,
  participation_rate: 0.8,
  ticks_recorded: 312,
  class_avg_score: 0.74,
  struggling_chapters: [
    { chapter_id: 1, chapter_name: 'Fractions', avg_score: 0.42, tick_count: 40 },
  ],
  strong_chapters: [{ chapter_id: 2, chapter_name: 'Algebra', avg_score: 0.88, tick_count: 60 }],
  model_used: 'claude-sonnet-4-6',
  generated_at: '2026-06-07T10:00:00Z',
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <WeeklyReportPanel subjectRoomId={1} />
    </QueryClientProvider>
  );
}

describe('WeeklyReportPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not fetch until expanded', () => {
    mockGet.mockResolvedValue({ data: REPORT });
    renderPanel();
    expect(screen.getByText('Weekly AI Summary')).toBeDefined();
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('labels a real LLM report as AI-generated', async () => {
    mockGet.mockResolvedValue({ data: REPORT });
    renderPanel();

    fireEvent.click(screen.getByText('Weekly AI Summary'));

    await waitFor(() => expect(screen.getByText(/improving in algebra/)).toBeDefined());
    expect(screen.getByText('✨ AI-generated')).toBeDefined();
  });

  it('marks a stub fallback as an auto-summary rather than AI output', async () => {
    mockGet.mockResolvedValue({ data: { ...REPORT, model_used: 'stub' } });
    renderPanel();

    fireEvent.click(screen.getByText('Weekly AI Summary'));

    await waitFor(() => expect(screen.getByText('Auto-summary')).toBeDefined());
    expect(screen.getByText(/AI was unavailable/)).toBeDefined();
    expect(screen.queryByText('✨ AI-generated')).toBeNull();
  });

  it('shows a shape-matched skeleton — not the empty state — while the report loads', async () => {
    let resolveGet!: (value: { data: WeeklyClassReport }) => void;
    mockGet.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveGet = resolve;
        })
    );
    renderPanel();

    fireEvent.click(screen.getByText('Weekly AI Summary'));

    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);
    expect(screen.queryByText(/No weekly summary yet/)).toBeNull();

    resolveGet({ data: REPORT });
    await waitFor(() => expect(screen.getByText(/improving in algebra/)).toBeDefined());
  });

  it('shows an error with retry — not the empty state — when the list fetch fails', async () => {
    mockGet.mockRejectedValue(new Error('network down'));
    renderPanel();

    fireEvent.click(screen.getByText('Weekly AI Summary'));

    await waitFor(() =>
      expect(screen.getByText(/Couldn't load the weekly summary just now/)).toBeDefined()
    );
    // A failed fetch must not read as "no report exists — go generate one".
    expect(screen.queryByText(/No weekly summary yet/)).toBeNull();
    expect(screen.getByRole('button', { name: /retry/i })).toBeDefined();
  });

  it('recovers when retry succeeds after a failed list fetch', async () => {
    mockGet.mockRejectedValueOnce(new Error('network down'));
    mockGet.mockResolvedValue({ data: REPORT });
    renderPanel();

    fireEvent.click(screen.getByText('Weekly AI Summary'));
    await waitFor(() =>
      expect(screen.getByText(/Couldn't load the weekly summary just now/)).toBeDefined()
    );

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => expect(screen.getByText(/improving in algebra/)).toBeDefined());
    expect(screen.queryByText(/Couldn't load the weekly summary just now/)).toBeNull();
  });

  it('surfaces an error when generation fails instead of silently reverting', async () => {
    mockGet.mockRejectedValue({ response: { status: 404 } });
    mockPost.mockRejectedValue(new Error('boom'));
    renderPanel();

    fireEvent.click(screen.getByText('Weekly AI Summary'));

    await waitFor(() => expect(screen.getByText(/No weekly summary yet/)).toBeDefined());
    fireEvent.click(screen.getByText('Generate'));

    await waitFor(() => expect(screen.getByText(/Couldn't generate the summary/)).toBeDefined());
  });
});
