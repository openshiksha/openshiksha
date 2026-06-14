import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { OpenResponseGradingPage } from './OpenResponseGradingPage';
import type { OpenResponseGrade } from './useOpenResponseGrading';

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

const ROOM = {
  id: 1,
  classroom: 1,
  classroom_display: 'Std 8 A',
  subject: 2,
  subject_name: 'Biology',
  teacher: 9,
  teacher_name: 'T',
  is_active: true,
  student_count: 30,
};

const GRADE: OpenResponseGrade = {
  id: 21,
  subpart: 301,
  question_text: 'Explain why leaves look green.',
  student: 42,
  student_name: 'Asha Rao',
  student_username: 'asha',
  subject_room: 1,
  subject_name: 'Biology',
  assignment: null,
  response_text: 'Chlorophyll absorbs red and blue light and reflects green.',
  status: 'ai_graded',
  max_marks: 5,
  suggested_score: 4,
  feedback: 'Correct mechanism; mention photosynthesis explicitly for full marks.',
  criterion_scores: [
    { label: 'Names chlorophyll', awarded: 2, max: 2, comment: 'Present.' },
    { label: 'Links to photosynthesis', awarded: 2, max: 3, comment: 'Implied, not named.' },
  ],
  confidence: 0.85,
  final_score: null,
  teacher_comment: '',
  reviewed_by: null,
  reviewed_at: null,
  effective_score: 4,
  is_reviewed: false,
  model_used: 'claude-sonnet-4-6',
  error_detail: '',
  created_at: '2026-06-11T08:00:00Z',
  updated_at: '2026-06-11T08:00:05Z',
};

// The page fires two GETs (subject rooms + grades) — route by URL.
function mockApi(grades: OpenResponseGrade[] | Promise<never>) {
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/subject-rooms/')) {
      return Promise.resolve({ data: { results: [ROOM] } });
    }
    if (grades instanceof Promise) return grades;
    return Promise.resolve({ data: { results: grades } });
  });
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <OpenResponseGradingPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('OpenResponseGradingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows skeletons — not the empty state — while the queue loads', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.startsWith('/subject-rooms/')) {
        return Promise.resolve({ data: { results: [ROOM] } });
      }
      return new Promise(() => {});
    });
    renderPage();

    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);
    expect(screen.queryByText(/no responses to grade yet/i)).toBeNull();
  });

  it('renders an AI-graded card: response, suggestion, confidence, criteria, provenance', async () => {
    mockApi([GRADE]);
    renderPage();

    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
    expect(screen.getByText(/chlorophyll absorbs red and blue light/i)).toBeDefined();
    expect(screen.getByText('AI suggests 4/5')).toBeDefined();
    expect(screen.getByText('85% confident')).toBeDefined();
    expect(screen.getByText('✨ AI-generated')).toBeDefined();
    expect(screen.getByText('Names chlorophyll')).toBeDefined();
    expect(screen.getByText('Needs your review')).toBeDefined();
  });

  it('accepting the suggestion posts review with the suggested score', async () => {
    const user = userEvent.setup();
    mockApi([GRADE]);
    mockPost.mockResolvedValue({
      data: { ...GRADE, status: 'reviewed', final_score: 4, is_reviewed: true },
    });
    renderPage();

    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
    await user.click(screen.getByRole('button', { name: /accept suggestion/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/open-grades/21/review/', { final_score: 4 })
    );
  });

  it('overriding the score relabels the action and posts the override + comment', async () => {
    const user = userEvent.setup();
    mockApi([GRADE]);
    mockPost.mockResolvedValue({
      data: { ...GRADE, status: 'reviewed', final_score: 3, is_reviewed: true },
    });
    renderPage();

    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());

    const scoreInput = screen.getByLabelText(/final marks/i);
    await user.clear(scoreInput);
    await user.type(scoreInput, '3');
    await user.type(screen.getByLabelText(/comment for the student/i), 'Name the process.');
    await user.click(screen.getByRole('button', { name: /save final grade/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/open-grades/21/review/', {
        final_score: 3,
        teacher_comment: 'Name the process.',
      })
    );
  });

  it('renders pending and failed cards with their working/retry affordances', async () => {
    mockApi([
      { ...GRADE, id: 22, status: 'pending', suggested_score: null },
      {
        ...GRADE,
        id: 23,
        status: 'failed',
        suggested_score: null,
        error_detail: 'Provider timeout.',
      },
    ]);
    renderPage();

    await waitFor(() => expect(screen.getByText(/AI is reading this response/i)).toBeDefined());
    expect(screen.getByText(/couldn't grade this response/i)).toBeDefined();
    expect(screen.getByText('Provider timeout.')).toBeDefined();
    expect(screen.getByRole('button', { name: /try again/i })).toBeDefined();
  });

  it('reviewed cards show the final grade and the override note', async () => {
    mockApi([
      {
        ...GRADE,
        status: 'reviewed',
        final_score: 3,
        teacher_comment: 'Name the process.',
        is_reviewed: true,
      },
    ]);
    renderPage();

    await waitFor(() => expect(screen.getByText('Final grade: 3/5')).toBeDefined());
    expect(screen.getByText(/AI suggested 4\/5 — you overrode it/)).toBeDefined();
    expect(screen.getByText(/name the process/i)).toBeDefined();
  });

  it('labels stub-graded suggestions as Auto-graded with a care note', async () => {
    mockApi([{ ...GRADE, model_used: 'stub' }]);
    renderPage();

    await waitFor(() => expect(screen.getByText('Auto-graded')).toBeDefined());
    expect(screen.getByText(/review with extra care/i)).toBeDefined();
    expect(screen.queryByText('✨ AI-generated')).toBeNull();
  });

  it('flags a low-confidence suggestion so the teacher double-checks before accepting', async () => {
    mockApi([{ ...GRADE, confidence: 0.42 }]);
    renderPage();

    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
    expect(screen.getByText('42% confident')).toBeDefined();
    expect(screen.getByText(/double-check before accepting/i)).toBeDefined();
  });

  it('does not show the low-confidence note when the AI is confident', async () => {
    mockApi([GRADE]); // confidence 0.85
    renderPage();

    await waitFor(() => expect(screen.getByText('85% confident')).toBeDefined());
    expect(screen.queryByText(/double-check before accepting/i)).toBeNull();
  });

  it('status filter chips re-query with the status param', async () => {
    const user = userEvent.setup();
    mockApi([GRADE]);
    renderPage();

    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
    await user.click(screen.getByRole('button', { name: 'Finalised' }));

    await waitFor(() =>
      expect(mockGet).toHaveBeenCalledWith('/ai/open-grades/?status=reviewed')
    );
  });

  it('shows an error with retry — not the empty state — when the queue fetch fails', async () => {
    const user = userEvent.setup();
    let failed = false;
    mockGet.mockImplementation((url: string) => {
      if (url.startsWith('/subject-rooms/')) {
        return Promise.resolve({ data: { results: [ROOM] } });
      }
      if (!failed) {
        failed = true;
        return Promise.reject(new Error('network down'));
      }
      return Promise.resolve({ data: { results: [GRADE] } });
    });
    renderPage();

    await waitFor(() =>
      expect(screen.getByText(/couldn't load the grading queue just now/i)).toBeDefined()
    );
    // A failed fetch must not read as "queue is clear".
    expect(screen.queryByText(/no responses to grade yet/i)).toBeNull();

    await user.click(screen.getByRole('button', { name: /retry/i }));
    await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
  });

  it('explains the feature on a successful empty queue', async () => {
    mockApi([]);
    renderPage();

    await waitFor(() => expect(screen.getByText(/no responses to grade yet/i)).toBeDefined());
    expect(screen.getByText(/AI will suggest a grade for your review/i)).toBeDefined();
  });
});
