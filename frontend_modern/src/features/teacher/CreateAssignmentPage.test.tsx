import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CreateAssignmentPage } from './CreateAssignmentPage';

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet, post: mockPost },
}));

const ROOM = {
  id: 5,
  classroom: 2,
  classroom_display: 'OpenShiksha Demo School - Std 10 - Div A',
  subject: 1,
  subject_name: 'Mathematics',
  teacher: 1,
  teacher_name: 'Demo Teacher',
  is_active: true,
  student_count: 3,
};

const SET = {
  id: 10,
  title: 'Quadratic Equations – Practice Set 1',
  description: 'Foundational practice.',
  number: 1,
  standard: 1,
  subject: 1,
  subject_name: 'Mathematics',
  chapter: 1,
  chapter_name: 'Quadratic Equations',
  question_count: 4,
  estimated_minutes: 20,
  is_active: true,
};

beforeEach(() => {
  mockGet.mockReset();
  mockGet.mockImplementation((url: string) => {
    if (url === '/subject-rooms/') return Promise.resolve({ data: { results: [ROOM] } });
    if (url.startsWith('/problem-sets/')) return Promise.resolve({ data: { results: [SET] } });
    return Promise.resolve({ data: { results: [] } });
  });
});

function renderAt(path: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <CreateAssignmentPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('CreateAssignmentPage deep-link preselection', () => {
  it('preselects the problem set from ?problemSet= and offers a student preview', async () => {
    renderAt('/teacher/assignments/new?problemSet=10');

    // The set title shows up in the live assignment preview once preselected.
    await waitFor(() =>
      expect(screen.getAllByText('Quadratic Equations – Practice Set 1').length).toBeGreaterThan(0),
    );

    // The "preview the actual questions as a student" link points at the
    // read-only preview route for this set.
    const link = await screen.findByRole('link', { name: /preview the actual questions/i });
    expect(link).toHaveAttribute('href', '/teacher/problem-sets/10/preview');
  });

  it('preselects the subject room from ?room=', async () => {
    renderAt('/teacher/assignments/new?room=5');

    // The room's classroom label appears in the preview hero once selected.
    await waitFor(() =>
      expect(
        screen.getAllByText(/OpenShiksha Demo School - Std 10 - Div A/).length,
      ).toBeGreaterThan(0),
    );
  });
});
