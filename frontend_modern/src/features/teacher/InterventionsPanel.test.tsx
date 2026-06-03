import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { InterventionsPanel } from './InterventionsPanel';
import type { InterventionSuggestion } from './useInterventions';

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

const SUGGESTION: InterventionSuggestion = {
  id: 7,
  subject_room: 1,
  subject_name: 'Mathematics',
  classroom_label: 'Std 8 A',
  student: 42,
  student_name: 'Asha Rao',
  student_username: 'asha',
  status: 'open',
  priority: 5,
  severity: 'severe',
  strategy_text: 'Re-teach long division with a fresh worked example.',
  avg_score: 0.22,
  gap_count: 2,
  focus_chapters: [
    { chapter_id: 1, chapter_name: 'Long Division', avg_score: 0.15, severity: 'severe' },
    { chapter_id: 2, chapter_name: 'Fractions', avg_score: 0.45, severity: 'mild' },
  ],
  misconception_labels: [{ label: 'adds numerators and denominators', count: 3 }],
  acknowledged_by: null,
  acknowledged_at: null,
  model_used: 'stub',
  generated_at: '2026-06-02T10:00:00Z',
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <InterventionsPanel subjectRoomId={1} />
    </QueryClientProvider>
  );
}

describe('InterventionsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not fetch until expanded', () => {
    mockGet.mockResolvedValue({ data: { results: [] } });
    renderPanel();
    expect(screen.getByText('Intervention Suggestions')).toBeDefined();
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('renders a suggestion card with student, strategy and chapters once expanded', async () => {
    mockGet.mockResolvedValue({ data: { results: [SUGGESTION] } });
    renderPanel();

    fireEvent.click(screen.getByText('Intervention Suggestions'));

    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
    expect(screen.getByText(/Re-teach long division/)).toBeDefined();
    expect(screen.getByText('Long Division')).toBeDefined();
    expect(screen.getByText(/adds numerators and denominators/)).toBeDefined();
    expect(screen.getByText('Priority 5')).toBeDefined();
  });

  it('posts an acknowledge status change when "Mark as planned" is clicked', async () => {
    mockGet.mockResolvedValue({ data: { results: [SUGGESTION] } });
    mockPost.mockResolvedValue({ data: {} });
    renderPanel();

    fireEvent.click(screen.getByText('Intervention Suggestions'));
    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());

    fireEvent.click(screen.getByText('Mark as planned'));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/interventions/7/set-status/', {
        status: 'acknowledged',
      })
    );
  });

  it('shows an empty state and a Generate action when there are no suggestions', async () => {
    mockGet.mockResolvedValue({ data: { results: [] } });
    mockPost.mockResolvedValue({ data: {} });
    renderPanel();

    fireEvent.click(screen.getByText('Intervention Suggestions'));

    await waitFor(() => expect(screen.getByText(/No struggling students flagged/)).toBeDefined());
    fireEvent.click(screen.getByText('Generate'));
    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/interventions/generate/', { subject_room_id: 1 })
    );
  });
});
