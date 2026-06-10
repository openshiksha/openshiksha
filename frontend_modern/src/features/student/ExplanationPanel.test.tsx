import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ExplanationPanel } from './ExplanationPanel';
import type { SubpartExplanation } from './useExplanation';

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

const EXPLANATION: SubpartExplanation = {
  id: 1,
  question_subpart: 101,
  question_text: 'What is 6 × 7?',
  subpart_index: 0,
  submission: 55,
  student_answer: '41',
  is_correct: false,
  explanation_text: 'Close — 6 × 7 is 42, not 41. Think of it as 6 × 7 = 6 × 5 + 6 × 2.',
  language: 'en',
  grade_level: 8,
  model_used: 'claude-haiku-4-5-20251001',
  generated_at: '2026-06-09T10:00:00Z',
};

function renderPanel(props?: Partial<Parameters<typeof ExplanationPanel>[0]>) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ExplanationPanel
        subpartId={101}
        studentAnswer="41"
        isCorrect={false}
        pollIntervalMs={10}
        maxPollAttempts={3}
        {...props}
      />
    </QueryClientProvider>
  );
}

describe('ExplanationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts collapsed and generates then polls until the explanation arrives', async () => {
    const user = userEvent.setup();
    // First two list calls: empty (pre-generate check + first poll); then ready.
    mockGet
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValue({ data: [EXPLANATION] });
    mockPost.mockResolvedValue({ data: { detail: 'queued' } });

    renderPanel();

    const trigger = screen.getByRole('button', { name: /explain this answer/i });
    expect(mockGet).not.toHaveBeenCalled();

    await user.click(trigger);
    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/explanations/generate/', {
        subpart_id: 101,
        student_answer: '41',
        is_correct: false,
      })
    );
    expect(screen.getByText(/writing your explanation/i)).toBeDefined();

    await waitFor(() => expect(screen.getByText(/6 × 7 is 42/)).toBeDefined());
    expect(screen.getByText('✨ AI-generated')).toBeDefined();
    expect(screen.getByText('Where this went wrong')).toBeDefined();
  });

  it('shows an existing explanation directly without re-generating', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: { results: [EXPLANATION] } });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /explain this answer/i }));

    await waitFor(() => expect(screen.getByText(/6 × 7 is 42/)).toBeDefined());
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('labels stub-generated explanations transparently', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [{ ...EXPLANATION, model_used: 'stub' }] });

    renderPanel({ isCorrect: true });
    await user.click(screen.getByRole('button', { name: /explain this answer/i }));

    await waitFor(() => expect(screen.getByText('Auto-explanation')).toBeDefined());
    expect(screen.queryByText('✨ AI-generated')).toBeNull();
    expect(screen.getByText('Why this answer is right')).toBeDefined();
    expect(screen.getByText(/without an AI model/i)).toBeDefined();
  });

  it('gives up after the poll budget with a friendly error and a working retry', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [] });
    mockPost.mockResolvedValue({ data: { detail: 'queued' } });

    renderPanel();
    await user.click(screen.getByRole('button', { name: /explain this answer/i }));

    await waitFor(
      () => expect(screen.getByText(/couldn't fetch an explanation just now/i)).toBeDefined(),
      { timeout: 3000 }
    );

    // Retry: the explanation is ready this time.
    mockGet.mockResolvedValue({ data: [EXPLANATION] });
    await user.click(screen.getByRole('button', { name: /retry/i }));
    await waitFor(() => expect(screen.getByText(/6 × 7 is 42/)).toBeDefined());
  });

  it('surfaces a generation failure instead of polling forever', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [] });
    mockPost.mockRejectedValue(new Error('rate limited'));

    renderPanel();
    await user.click(screen.getByRole('button', { name: /explain this answer/i }));

    await waitFor(() =>
      expect(screen.getByText(/couldn't fetch an explanation just now/i)).toBeDefined()
    );
  });
});
