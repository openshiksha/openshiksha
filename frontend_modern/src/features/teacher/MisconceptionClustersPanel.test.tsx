import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MisconceptionClustersPanel } from './MisconceptionClustersPanel';
import type { MisconceptionCluster } from './useMisconceptionClusters';

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

const CLUSTER: MisconceptionCluster = {
  id: 3,
  subject_room: 1,
  subject_name: 'Mathematics',
  misconception_label: 'Adds denominators when adding fractions',
  student_count: 4,
  occurrence_count: 11,
  sample_diagnosis: 'Students treat 1/2 + 1/3 as 2/5 by adding tops and bottoms separately.',
  sample_remediation_tip: 'Re-derive common denominators with a fraction-wall visual.',
  window_start: '2026-05-10',
  last_seen: '2026-06-08T10:00:00Z',
  refreshed_at: '2026-06-09T06:00:00Z',
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MisconceptionClustersPanel subjectRoomId={1} />
    </QueryClientProvider>
  );
}

describe('MisconceptionClustersPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('is collapsed by default and only fetches when opened', async () => {
    const user = userEvent.setup();
    let resolveGet!: (value: { data: { results: MisconceptionCluster[] } }) => void;
    mockGet.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveGet = resolve;
        })
    );

    renderPanel();
    expect(mockGet).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));
    // Shape-matched skeleton cards, not bare text, while the list loads.
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);
    expect(screen.queryByText(/no misconception patterns detected yet/i)).toBeNull();

    resolveGet({ data: { results: [CLUSTER] } });
    await waitFor(() =>
      expect(screen.getByText('Adds denominators when adding fractions')).toBeDefined()
    );
    expect(mockGet).toHaveBeenCalledWith('/ai/misconception-clusters/?subject_room=1');
  });

  it('renders cluster details: affected students, diagnosis, tip, occurrences', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [CLUSTER] });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));

    await waitFor(() => expect(screen.getByText('4 students')).toBeDefined());
    expect(screen.getByText(/treat 1\/2 \+ 1\/3 as 2\/5/)).toBeDefined();
    expect(screen.getByText(/fraction-wall visual/)).toBeDefined();
    expect(screen.getByText(/Seen 11 times/)).toBeDefined();
  });

  it('explains what unlocks clusters when there are none yet', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [] });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));

    await waitFor(() =>
      expect(screen.getByText(/no misconception patterns detected yet/i)).toBeDefined()
    );
  });

  it('shows an error with retry — not the empty state — when the list fetch fails', async () => {
    const user = userEvent.setup();
    mockGet.mockRejectedValue(new Error('network down'));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));

    await waitFor(() =>
      expect(screen.getByText(/couldn't load misconception patterns/i)).toBeDefined()
    );
    // A failed fetch must not read as "your class has no misconceptions".
    expect(screen.queryByText(/no misconception patterns detected yet/i)).toBeNull();
    expect(screen.getByRole('button', { name: /retry/i })).toBeDefined();
  });

  it('recovers when retry succeeds after a failed list fetch', async () => {
    const user = userEvent.setup();
    mockGet.mockRejectedValueOnce(new Error('network down'));
    mockGet.mockResolvedValue({ data: [CLUSTER] });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));
    await waitFor(() =>
      expect(screen.getByText(/couldn't load misconception patterns/i)).toBeDefined()
    );

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() =>
      expect(screen.getByText('Adds denominators when adding fractions')).toBeDefined()
    );
    expect(screen.queryByText(/couldn't load misconception patterns/i)).toBeNull();
  });

  it('queues a refresh and confirms the recompute is underway', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [CLUSTER] });
    mockPost.mockResolvedValue({ data: { detail: 'queued' } });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));
    await waitFor(() => expect(screen.getByText('4 students')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/misconception-clusters/refresh/', {
        subject_room_id: 1,
      })
    );
    await waitFor(() => expect(screen.getByRole('status')).toBeDefined());
  });

  it('clears the "Recomputing…" confirmation after a short delay', async () => {
    // Spy on the dismiss timer rather than running fake timers (happy-dom +
    // userEvent + waitFor don't compose with fake timers). We capture the
    // scheduled self-dismiss callback and invoke it directly.
    const setTimeoutSpy = vi.spyOn(globalThis, 'setTimeout');
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [CLUSTER] });
    mockPost.mockResolvedValue({ data: { detail: 'queued' } });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));
    await waitFor(() => expect(screen.getByText('4 students')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /refresh/i }));
    await waitFor(() =>
      expect(screen.getByText(/recomputing from recent submissions/i)).toBeDefined()
    );

    // Pull the 6s self-dismiss callback the panel scheduled and fire it.
    const dismiss = setTimeoutSpy.mock.calls.find(([, delay]) => delay === 6000)?.[0] as
      | (() => void)
      | undefined;
    expect(dismiss).toBeDefined();
    act(() => dismiss!());

    await waitFor(() =>
      expect(screen.queryByText(/recomputing from recent submissions/i)).toBeNull()
    );
    setTimeoutSpy.mockRestore();
  });

  it('shows an inline error when the refresh fails', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [CLUSTER] });
    mockPost.mockRejectedValue(new Error('boom'));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /class misconceptions/i }));
    await waitFor(() => expect(screen.getByText('4 students')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() => expect(screen.getByText(/couldn't refresh just now/i)).toBeDefined());
  });
});
