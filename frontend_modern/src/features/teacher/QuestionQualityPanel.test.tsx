import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QuestionQualityPanel } from './QuestionQualityPanel';
import type { CalibrationSummary, DifficultyCalibration } from './useDifficultyCalibration';

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

const CALIBRATION: DifficultyCalibration = {
  id: 7,
  subject_room: 1,
  subject_name: 'Mathematics',
  question_subpart: 42,
  question_id: 42,
  subpart_index: 0,
  chapter_name: 'Fractions',
  question_preview: 'Add 1/2 and 1/3 and simplify the result.',
  sample_size: 18,
  attempt_count: 21,
  facility_index: 0.17,
  discrimination_index: 0.05,
  empirical_difficulty: 5,
  declared_difficulty: 2,
  difficulty_delta: 3,
  flag: 'too_hard',
  flag_display: 'Too hard',
  needs_review: true,
  computed_at: '2026-06-10T06:00:00Z',
};

const SUMMARY: CalibrationSummary = {
  subject_room: 1,
  total_calibrated: 12,
  flagged: 1,
  by_flag: { ok: 11, mislabeled: 0, too_easy: 0, too_hard: 1, low_discrimination: 0 },
};

/** Serve the list and summary endpoints; the panel queries both when opened. */
const serveList = (listResponse: () => Promise<{ data: { results: DifficultyCalibration[] } }>) => {
  mockGet.mockImplementation((url: string) =>
    url.includes('/summary/') ? Promise.resolve({ data: SUMMARY }) : listResponse()
  );
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <QuestionQualityPanel subjectRoomId={1} />
    </QueryClientProvider>
  );
}

describe('QuestionQualityPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('is collapsed by default and shows shape-matched skeletons while loading', async () => {
    const user = userEvent.setup();
    let resolveList!: (value: { data: { results: DifficultyCalibration[] } }) => void;
    serveList(
      () =>
        new Promise((resolve) => {
          resolveList = resolve;
        })
    );

    renderPanel();
    expect(mockGet).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /question quality/i }));
    // Shape-matched skeleton cards, not bare text, while the list loads.
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);
    expect(screen.queryByText(/no questions flagged yet/i)).toBeNull();

    resolveList({ data: { results: [CALIBRATION] } });
    await waitFor(() =>
      expect(screen.getByText('Add 1/2 and 1/3 and simplify the result.')).toBeDefined()
    );
    expect(mockGet).toHaveBeenCalledWith(
      '/ai/difficulty-calibrations/?subject_room=1&needs_review=true'
    );
  });

  it('renders the flag verdict, teacher hint, and authored-vs-observed chips', async () => {
    const user = userEvent.setup();
    serveList(() => Promise.resolve({ data: { results: [CALIBRATION] } }));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /question quality/i }));

    await waitFor(() => expect(screen.getByText('Too hard')).toBeDefined());
    expect(screen.getByText(/almost no one got this right/i)).toBeDefined();
    expect(screen.getByText('Authored difficulty')).toBeDefined();
    expect(screen.getByText('Observed difficulty')).toBeDefined();
    expect(screen.getByText(/1 of 12 calibrated questions need a look/i)).toBeDefined();
  });

  it('explains what unlocks calibration when nothing is flagged', async () => {
    const user = userEvent.setup();
    serveList(() => Promise.resolve({ data: { results: [] } }));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /question quality/i }));

    await waitFor(() => expect(screen.getByText(/no questions flagged yet/i)).toBeDefined());
  });

  it('shows an error with retry — not the empty state — when the list fetch fails', async () => {
    const user = userEvent.setup();
    serveList(() => Promise.reject(new Error('network down')));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /question quality/i }));

    await waitFor(() =>
      expect(screen.getByText(/couldn't load the question analysis/i)).toBeDefined()
    );
    // A failed fetch must not read as "your question bank is healthy".
    expect(screen.queryByText(/no questions flagged yet/i)).toBeNull();
    expect(screen.getByRole('button', { name: /retry/i })).toBeDefined();
  });

  it('recovers when retry succeeds after a failed list fetch', async () => {
    const user = userEvent.setup();
    let failNext = true;
    serveList(() => {
      if (failNext) {
        failNext = false;
        return Promise.reject(new Error('network down'));
      }
      return Promise.resolve({ data: { results: [CALIBRATION] } });
    });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /question quality/i }));
    await waitFor(() =>
      expect(screen.getByText(/couldn't load the question analysis/i)).toBeDefined()
    );

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() =>
      expect(screen.getByText('Add 1/2 and 1/3 and simplify the result.')).toBeDefined()
    );
    expect(screen.queryByText(/couldn't load the question analysis/i)).toBeNull();
  });

  it('queues a recalibration and confirms the recompute is underway', async () => {
    const user = userEvent.setup();
    serveList(() => Promise.resolve({ data: { results: [CALIBRATION] } }));
    mockPost.mockResolvedValue({ data: { detail: 'queued' } });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /question quality/i }));
    await waitFor(() => expect(screen.getByText('Too hard')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/difficulty-calibrations/refresh/', {
        subject_room_id: 1,
      })
    );
    await waitFor(() =>
      expect(screen.getByText(/recalibrating from recent answers/i)).toBeDefined()
    );
  });

  it('shows an inline error when the recalibration fails to start', async () => {
    const user = userEvent.setup();
    serveList(() => Promise.resolve({ data: { results: [CALIBRATION] } }));
    mockPost.mockRejectedValue(new Error('boom'));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /question quality/i }));
    await waitFor(() => expect(screen.getByText('Too hard')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() =>
      expect(screen.getByText(/couldn't start the recalibration/i)).toBeDefined()
    );
  });
});
