import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AssignmentDraftsPanel } from './AssignmentDraftsPanel';
import type { AssignmentDraft } from './useAssignmentDrafts';

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

const READY_DRAFT: AssignmentDraft = {
  id: 11,
  subject_room: 1,
  subject_name: 'Mathematics',
  classroom_label: 'Std 8 A',
  status: 'ready',
  title: 'Practice: Fractions',
  rationale_text: 'The class averages 42% on Fractions; these 8 questions target that gap.',
  target_difficulty: 2,
  requested_size: 8,
  target_chapters: [
    { chapter_id: 1, chapter_name: 'Fractions', avg_score: 0.42, tick_count: 40 },
    { chapter_id: 2, chapter_name: 'Decimals', avg_score: 0.55, tick_count: 22 },
  ],
  selected_questions: [
    {
      question_id: 5,
      chapter_id: 1,
      chapter_name: 'Fractions',
      difficulty: 2,
      question_type: 'mcq',
      preview: 'What is 1/2 + 1/3?',
      reason: 'targets Fractions (42% avg)',
    },
  ],
  question_count: 8,
  estimated_minutes: 24,
  is_actionable: true,
  approved_problem_set: null,
  approved_assignment: null,
  model_used: 'claude-sonnet-4-6',
  error_detail: '',
  created_at: '2026-06-10T08:00:00Z',
  updated_at: '2026-06-10T08:00:05Z',
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AssignmentDraftsPanel subjectRoomId={1} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

async function expandPanel(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /ai assignment drafts/i }));
}

describe('AssignmentDraftsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('is collapsed by default and shows skeletons — not the empty state — while loading', async () => {
    const user = userEvent.setup();
    let resolveGet!: (value: { data: { results: AssignmentDraft[] } }) => void;
    mockGet.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveGet = resolve;
        })
    );

    renderPanel();
    expect(mockGet).not.toHaveBeenCalled();

    await expandPanel(user);
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);
    expect(screen.queryByText(/no drafts yet/i)).toBeNull();

    resolveGet({ data: { results: [READY_DRAFT] } });
    await waitFor(() => expect(screen.getByText('Practice: Fractions')).toBeDefined());
    expect(mockGet).toHaveBeenCalledWith('/ai/assignment-drafts/?subject_room=1');
  });

  it('explains what the feature does when there are no drafts', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [] });

    renderPanel();
    await expandPanel(user);

    await waitFor(() => expect(screen.getByText(/no drafts yet/i)).toBeDefined());
    expect(screen.getByRole('button', { name: /draft an assignment/i })).toBeDefined();
  });

  it('renders a ready draft: rationale, chapter chips, counts and provenance badge', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [READY_DRAFT] });

    renderPanel();
    await expandPanel(user);

    await waitFor(() => expect(screen.getByText('Practice: Fractions')).toBeDefined());
    expect(screen.getByText(/averages 42% on Fractions/)).toBeDefined();
    expect(screen.getByText('Fractions')).toBeDefined();
    expect(screen.getByText('Decimals')).toBeDefined();
    expect(screen.getByText(/8 questions · ~24 min/)).toBeDefined();
    expect(screen.getByText('✨ AI-generated')).toBeDefined();
    expect(screen.getByRole('button', { name: /approve/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /dismiss/i })).toBeDefined();
  });

  it('labels a stub-built draft as Auto-drafted with a fallback note', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [{ ...READY_DRAFT, model_used: 'stub' }] });

    renderPanel();
    await expandPanel(user);

    await waitFor(() => expect(screen.getByText('Auto-drafted')).toBeDefined());
    expect(screen.getByText(/AI was unavailable/)).toBeDefined();
    expect(screen.queryByText('✨ AI-generated')).toBeNull();
  });

  it('generate posts the request and shows the pending card while assembly runs', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValueOnce({ data: [] });
    mockPost.mockResolvedValue({ data: { ...READY_DRAFT, id: 12, status: 'pending' } });
    mockGet.mockResolvedValue({ data: [{ ...READY_DRAFT, id: 12, status: 'pending' }] });

    renderPanel();
    await expandPanel(user);
    await waitFor(() => expect(screen.getByText(/no drafts yet/i)).toBeDefined());

    await user.click(screen.getByRole('button', { name: /draft an assignment/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/assignment-drafts/generate/', {
        subject_room_id: 1,
        size: 8,
        target_difficulty: 2,
      })
    );
    await waitFor(() =>
      expect(screen.getByText(/assembling a draft from your class's weak spots/i)).toBeDefined()
    );
  });

  it('approve happy path: posts due date and links to the created assignment', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValueOnce({ data: [READY_DRAFT] });
    const approved = {
      ...READY_DRAFT,
      status: 'approved' as const,
      approved_problem_set: 31,
      approved_assignment: 77,
    };
    mockPost.mockResolvedValue({ data: approved });
    mockGet.mockResolvedValue({ data: [approved] });

    renderPanel();
    await expandPanel(user);
    await waitFor(() => expect(screen.getByText('Practice: Fractions')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /approve/i }));
    await user.click(screen.getByRole('button', { name: /assign to class/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith(
        '/ai/assignment-drafts/11/approve/',
        expect.objectContaining({ due_at: expect.stringMatching(/T/) })
      )
    );
    await waitFor(() => expect(screen.getByText('Assigned')).toBeDefined());
    const link = screen.getByRole('link', { name: /view the assignment/i });
    expect(link.getAttribute('href')).toBe('/teacher/assignments/77');
  });

  it('approve conflict (409) surfaces the server detail instead of failing silently', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({ data: [READY_DRAFT] });
    mockPost.mockRejectedValue({
      response: {
        status: 409,
        data: { detail: "None of the draft's questions are still active. Regenerate the draft." },
      },
    });

    renderPanel();
    await expandPanel(user);
    await waitFor(() => expect(screen.getByText('Practice: Fractions')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /approve/i }));
    await user.click(screen.getByRole('button', { name: /assign to class/i }));

    await waitFor(() =>
      expect(screen.getByText(/none of the draft's questions are still active/i)).toBeDefined()
    );
  });

  it('dismiss posts and the card leaves the list', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValueOnce({ data: [READY_DRAFT] });
    const dismissed = { ...READY_DRAFT, status: 'dismissed' as const };
    mockPost.mockResolvedValue({ data: dismissed });
    mockGet.mockResolvedValue({ data: [dismissed] });

    renderPanel();
    await expandPanel(user);
    await waitFor(() => expect(screen.getByText('Practice: Fractions')).toBeDefined());

    await user.click(screen.getByRole('button', { name: /dismiss/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/assignment-drafts/11/dismiss/', {})
    );
    await waitFor(() => expect(screen.queryByText('Practice: Fractions')).toBeNull());
  });

  it('renders a failed draft with its error detail and a retry action', async () => {
    const user = userEvent.setup();
    mockGet.mockResolvedValue({
      data: [
        {
          ...READY_DRAFT,
          status: 'failed' as const,
          error_detail: 'Not enough practice data in this room yet.',
        },
      ],
    });

    renderPanel();
    await expandPanel(user);

    await waitFor(() =>
      expect(screen.getByText(/couldn't put this draft together/i)).toBeDefined()
    );
    expect(screen.getByText(/not enough practice data/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /try again/i })).toBeDefined();
  });

  it('shows an error with retry — not the empty state — when the list fetch fails', async () => {
    const user = userEvent.setup();
    mockGet.mockRejectedValueOnce(new Error('network down'));
    mockGet.mockResolvedValue({ data: [READY_DRAFT] });

    renderPanel();
    await expandPanel(user);

    await waitFor(() => expect(screen.getByText(/couldn't load drafts just now/i)).toBeDefined());
    expect(screen.queryByText(/no drafts yet/i)).toBeNull();

    await user.click(screen.getByRole('button', { name: /retry/i }));
    await waitFor(() => expect(screen.getByText('Practice: Fractions')).toBeDefined());
  });
});
