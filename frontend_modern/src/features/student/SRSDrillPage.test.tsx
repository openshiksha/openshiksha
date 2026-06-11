import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { SRSDrillPage } from './SRSDrillPage';
import type { SRSDrillData } from './useSRSDrill';

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

// The drill page only forwards answers into QuestionCard; the card's own
// rendering (KaTeX, option shuffling) and the ExplanationPanel behaviour
// (generate → poll → explanation / error+retry) are covered by their own
// test files. Here we assert the page-level wiring: result screens render
// the cards read-only with the explanationScore that unlocks the per-subpart
// "Explain this answer" affordance (ASA-8).
vi.mock('./QuestionCard', () => ({
  QuestionCard: ({
    onAnswerChange,
    isSubmitted,
    explanationScore,
  }: {
    onAnswerChange: (subpartId: number, value: string) => void;
    isSubmitted: boolean;
    explanationScore?: number | null;
  }) =>
    isSubmitted ? (
      <p>
        submitted-card score:
        {explanationScore === undefined ? 'undefined' : String(explanationScore)}
      </p>
    ) : (
      <button type="button" onClick={() => onAnswerChange(101, '42')}>
        Answer subpart
      </button>
    ),
}));

const DRILL: SRSDrillData = {
  entry_id: 7,
  chapter_name: 'Polynomials',
  subject_name: 'Mathematics',
  questions: [
    {
      id: 1,
      subparts: [{ id: 101 }],
    } as unknown as SRSDrillData['questions'][number],
  ],
};

const REVIEW_RESULT = {
  id: 7,
  knowledge_node: 3,
  chapter_name: 'Polynomials',
  interval_days: 12,
  easiness_factor: 2.5,
  repetitions: 3,
  next_review_date: '2026-06-21',
  last_reviewed_at: '2026-06-09T10:00:00Z',
  score: 0.8,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/student/srs-drill/7']}>
        <Routes>
          <Route path="/student/srs-drill/:entryId" element={<SRSDrillPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('SRSDrillPage repeat-review guard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ data: DRILL });
    mockPost.mockResolvedValue({ data: REVIEW_RESULT });
  });

  it('first submit marks the review and shows the graded result', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Submit Review' }));

    await waitFor(() => expect(screen.getByText('Great review!')).toBeDefined());
    expect(mockPost).toHaveBeenCalledTimes(1);
    expect(mockPost).toHaveBeenCalledWith('/ai/spaced-repetition/7/mark-reviewed/', {
      answers: { '101': '42' },
    });
    expect(screen.getByText(/Next review scheduled for 2026-06-21/)).toBeDefined();
    expect(screen.getByRole('button', { name: 'Practice again' })).toBeDefined();
    expect(screen.getByText(/Extra practice won't change your review schedule/)).toBeDefined();
  });

  it('a second pass in the same sitting never fires mark-reviewed again', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Submit Review' }));
    await waitFor(() => expect(screen.getByText('Great review!')).toBeDefined());

    await user.click(screen.getByRole('button', { name: 'Practice again' }));

    // Practice round: banner + relabelled submit.
    expect(
      screen.getByText(/Practice round — extra practice won't change your review schedule/)
    ).toBeDefined();
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Finish Practice' }));

    await waitFor(() => expect(screen.getByText('Practice round complete!')).toBeDefined());
    expect(screen.getByText(/your next review stays on 2026-06-21/)).toBeDefined();
    // The SM-2 update ran exactly once, on the first pass.
    expect(mockPost).toHaveBeenCalledTimes(1);
  });

  it('can chain further practice rounds without ever re-marking', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Submit Review' }));
    await waitFor(() => expect(screen.getByText('Great review!')).toBeDefined());

    for (let round = 0; round < 2; round++) {
      await user.click(screen.getByRole('button', { name: 'Practice again' }));
      await user.click(screen.getByText('Answer subpart'));
      await user.click(screen.getByRole('button', { name: 'Finish Practice' }));
      await waitFor(() => expect(screen.getByText('Practice round complete!')).toBeDefined());
    }

    expect(mockPost).toHaveBeenCalledTimes(1);
  });
});

describe('SRSDrillPage result-screen explanations (ASA-8)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ data: DRILL });
    mockPost.mockResolvedValue({ data: REVIEW_RESULT });
  });

  it('does not render the answer review while the drill is in progress', async () => {
    renderPage();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    expect(screen.queryByText('Go over your answers')).toBeNull();
    expect(screen.queryByText(/submitted-card/)).toBeNull();
  });

  it('review result shows the answered questions with the graded score for explanations', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Submit Review' }));
    await waitFor(() => expect(screen.getByText('Great review!')).toBeDefined());

    expect(screen.getByText('Go over your answers')).toBeDefined();
    // The graded score flows into QuestionCard, which unlocks the per-subpart
    // ExplanationPanel affordance exactly as on assignments (ASA-4).
    expect(screen.getByText(/submitted-card score:0\.8/)).toBeDefined();
  });

  it('practice result shows the answer review with a null score (round is ungraded)', async () => {
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => expect(screen.getByText('Polynomials')).toBeDefined());
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Submit Review' }));
    await waitFor(() => expect(screen.getByText('Great review!')).toBeDefined());

    await user.click(screen.getByRole('button', { name: 'Practice again' }));
    await user.click(screen.getByText('Answer subpart'));
    await user.click(screen.getByRole('button', { name: 'Finish Practice' }));
    await waitFor(() => expect(screen.getByText('Practice round complete!')).toBeDefined());

    expect(screen.getByText('Go over your answers')).toBeDefined();
    expect(screen.getByText(/submitted-card score:null/)).toBeDefined();
  });
});
