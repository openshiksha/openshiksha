import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { RecordResponsePanel } from './RecordResponsePanel';
import type { OpenResponseRubric } from './useOpenRubrics';

const { mockGet, mockPost, mockPatch } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPatch: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
    patch: mockPatch,
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

const RUBRIC: OpenResponseRubric = {
  id: 5,
  subpart: 301,
  question_text: 'Explain why leaves look green.',
  max_marks: 5,
  model_answer: 'Chlorophyll absorbs red and blue light and reflects green.',
  criteria: [{ label: 'Names chlorophyll', marks: 2 }],
  created_by: 9,
  created_at: '2026-06-11T08:00:00Z',
  updated_at: '2026-06-11T08:00:00Z',
};

function mockApi({ rubrics = [] as OpenResponseRubric[] } = {}) {
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/subject-rooms/1/students/')) {
      return Promise.resolve({
        data: { results: [{ id: 42, full_name: 'Asha Rao', username: 'asha' }] },
      });
    }
    if (url.startsWith('/subject-rooms/')) {
      return Promise.resolve({ data: { results: [ROOM] } });
    }
    if (url.startsWith('/questions/')) {
      return Promise.resolve({
        data: {
          results: [
            { id: 7, subparts: [{ id: 301, question_text: 'Explain why leaves look green.' }] },
          ],
        },
      });
    }
    if (url.startsWith('/ai/open-rubrics/')) {
      return Promise.resolve({ data: { results: rubrics } });
    }
    return Promise.reject(new Error(`unexpected GET ${url}`));
  });
}

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <RecordResponsePanel />
    </QueryClientProvider>
  );
}

async function fillSelections(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByText(/record a response for ai grading/i));
  await waitFor(() => expect(screen.getByText(/Biology · Std 8 A/)).toBeDefined());
  await user.selectOptions(screen.getByRole('combobox', { name: 'Class' }), '1');
  await waitFor(() => expect(screen.getByText('Asha Rao')).toBeDefined());
  await user.selectOptions(screen.getByRole('combobox', { name: 'Student' }), '42');
  await user.selectOptions(
    screen.getByRole('combobox', { name: 'Short-answer question' }),
    '301'
  );
}

describe('RecordResponsePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the panel header in Hindi when the locale is हिं', async () => {
    mockApi();
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <I18nProvider initialLocale="hi">
          <RecordResponsePanel />
        </I18nProvider>
      </QueryClientProvider>,
    );
    // "AI ग्रेडिंग के लिए उत्तर दर्ज करें" — the collapsed header.
    await waitFor(() => {
      expect(screen.getByText(/AI ग्रेडिंग के लिए उत्तर दर्ज करें/)).toBeInTheDocument();
    });
  });

  it('is collapsed by default and fetches nothing until opened', () => {
    mockApi();
    renderPanel();
    // useSubjectRooms fires on mount (shared with the page); nothing else should.
    expect(mockGet).not.toHaveBeenCalledWith(expect.stringContaining('/questions/'));
    expect(screen.queryByLabelText(/student's answer/i)).toBeNull();
  });

  it('submits a response: room → student → subpart → answer → 202 + success note', async () => {
    const user = userEvent.setup();
    mockApi({ rubrics: [RUBRIC] });
    mockPost.mockResolvedValue({ data: { id: 99, status: 'pending' } });
    renderPanel();

    await fillSelections(user);
    await user.type(screen.getByLabelText(/student's answer/i), 'Because of chlorophyll.');
    await user.click(screen.getByRole('button', { name: /send to ai grading/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/open-grades/submit/', {
        subject_room_id: 1,
        student_id: 42,
        subpart_id: 301,
        response_text: 'Because of chlorophyll.',
      })
    );
    await waitFor(() => expect(screen.getByText(/queued — it appears below/i)).toBeDefined());
  });

  it('nudges to add a rubric when the picked subpart has none', async () => {
    const user = userEvent.setup();
    mockApi({ rubrics: [] });
    renderPanel();

    await fillSelections(user);

    await waitFor(() => expect(screen.getByText(/no rubric yet/i)).toBeDefined());
    expect(screen.getByRole('button', { name: /add rubric/i })).toBeDefined();
  });

  it('creates a rubric with model answer and marking points', async () => {
    const user = userEvent.setup();
    mockApi({ rubrics: [] });
    mockPost.mockResolvedValue({ data: RUBRIC });
    renderPanel();

    await fillSelections(user);
    await waitFor(() => expect(screen.getByText(/no rubric yet/i)).toBeDefined());
    await user.click(screen.getByRole('button', { name: /add rubric/i }));

    await user.type(screen.getByLabelText(/model answer/i), 'Chlorophyll reflects green.');
    await user.click(screen.getByRole('button', { name: /\+ marking point/i }));
    await user.type(screen.getByLabelText('Criterion 1 label'), 'Names chlorophyll');
    await user.click(screen.getByRole('button', { name: /save rubric/i }));

    await waitFor(() =>
      expect(mockPost).toHaveBeenCalledWith('/ai/open-rubrics/', {
        subpart: 301,
        max_marks: 5,
        model_answer: 'Chlorophyll reflects green.',
        criteria: [{ label: 'Names chlorophyll', marks: 1 }],
      })
    );
  });

  it('shows the existing rubric summary and PATCHes on edit', async () => {
    const user = userEvent.setup();
    mockApi({ rubrics: [RUBRIC] });
    mockPatch.mockResolvedValue({ data: { ...RUBRIC, max_marks: 6 } });
    renderPanel();

    await fillSelections(user);
    await waitFor(() => expect(screen.getByText(/rubric:/i)).toBeDefined());
    expect(screen.getByText(/5 marks · 1 marking point/)).toBeDefined();

    await user.click(screen.getByRole('button', { name: /edit/i }));
    const marks = screen.getByLabelText(/maximum marks/i);
    await user.clear(marks);
    await user.type(marks, '6');
    await user.click(screen.getByRole('button', { name: /update rubric/i }));

    await waitFor(() =>
      expect(mockPatch).toHaveBeenCalledWith(
        '/ai/open-rubrics/5/',
        expect.objectContaining({ max_marks: 6 })
      )
    );
  });

  it('warns when marking points do not sum to the maximum marks', async () => {
    const user = userEvent.setup();
    mockApi({ rubrics: [RUBRIC] });
    renderPanel();

    await fillSelections(user);
    await waitFor(() => expect(screen.getByText(/rubric:/i)).toBeDefined());
    await user.click(screen.getByRole('button', { name: /edit/i }));

    // Existing criterion is 2 marks against a 5-mark maximum.
    expect(screen.getByText(/add up to 2, not 5/i)).toBeDefined();
  });

  it('surfaces a submit failure instead of silently dropping the response', async () => {
    const user = userEvent.setup();
    mockApi({ rubrics: [RUBRIC] });
    mockPost.mockRejectedValue(new Error('boom'));
    renderPanel();

    await fillSelections(user);
    await user.type(screen.getByLabelText(/student's answer/i), 'Because of chlorophyll.');
    await user.click(screen.getByRole('button', { name: /send to ai grading/i }));

    await waitFor(() =>
      expect(screen.getByText(/couldn't queue this response just now/i)).toBeDefined()
    );
  });
});
