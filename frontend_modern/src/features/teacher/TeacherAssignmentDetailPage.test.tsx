import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { TeacherAssignmentDetailPage } from './TeacherAssignmentDetailPage';
import type { Assignment, ProblemSet } from '@/types/index';

const { mockGet, mockPatch, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPatch: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet, patch: mockPatch, post: mockPost },
}));

const STUB_PS = {
  id: 1,
  title: 'Algebra #1',
  subject: 1,
  subject_name: 'Math',
  chapter: 1,
  chapter_name: 'Algebra',
  standard: 8,
  question_count: 5,
  estimated_minutes: 20,
  created_by: 1,
  created_at: '2026-01-01',
} as unknown as ProblemSet;

function makeAssignment(overrides: Partial<Assignment> = {}): Assignment {
  return {
    id: 7,
    subject_room: 1,
    subject_room_display: 'Std 8 A · Math',
    problem_set: STUB_PS,
    assigned_by: 1,
    assigned_at: '2026-06-01T00:00:00Z',
    due_at: '2026-06-10T10:00:00Z',
    number: 1,
    average_score: null,
    completion_rate: 0.2,
    submission_count: 2,
    student_count: 10,
    closed_at: null,
    status: 'active',
    ...overrides,
  };
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/teacher/assignments/7']}>
        <Routes>
          <Route path="/teacher/assignments/:id" element={<TeacherAssignmentDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  mockGet.mockReset();
  mockPatch.mockReset();
  mockPost.mockReset();
});

describe('TeacherAssignmentDetailPage — lifecycle controls', () => {
  it('renders the Active badge and Close button when assignment is active', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/submissions')) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: makeAssignment() });
    });
    renderPage();
    expect(await screen.findByText('Active')).toBeInTheDocument();
    expect(screen.getByTestId('close-button')).toBeInTheDocument();
  });

  it('renders the Closed badge and Reopen button when assignment is closed', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/submissions')) return Promise.resolve({ data: [] });
      return Promise.resolve({
        data: makeAssignment({ status: 'closed', closed_at: '2026-06-08T00:00:00Z' }),
      });
    });
    renderPage();
    expect(await screen.findByText('Closed')).toBeInTheDocument();
    expect(screen.getByTestId('reopen-button')).toBeInTheDocument();
    expect(screen.queryByTestId('close-button')).not.toBeInTheDocument();
  });

  it('PATCHes the due date when Save due date is clicked', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/submissions')) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: makeAssignment() });
    });
    mockPatch.mockResolvedValue({ data: makeAssignment({ due_at: '2026-07-01T10:00:00Z' }) });
    renderPage();
    const input = (await screen.findByTestId('due-at-input')) as HTMLInputElement;
    fireEvent.change(input, { target: { value: '2026-07-01T10:00' } });
    fireEvent.click(screen.getByTestId('due-at-save'));
    await waitFor(() => {
      expect(mockPatch).toHaveBeenCalledWith(
        '/assignments/7/',
        expect.objectContaining({ due_at: expect.any(String) }),
      );
    });
  });

  it('POSTs to /close/ when Close is clicked', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/submissions')) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: makeAssignment() });
    });
    mockPost.mockResolvedValue({
      data: makeAssignment({ status: 'closed', closed_at: '2026-06-08T00:00:00Z' }),
    });
    renderPage();
    fireEvent.click(await screen.findByTestId('close-button'));
    await waitFor(() => expect(mockPost).toHaveBeenCalledWith('/assignments/7/close/'));
  });

  it('POSTs to /reopen/ when Reopen is clicked', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/submissions')) return Promise.resolve({ data: [] });
      return Promise.resolve({
        data: makeAssignment({ status: 'closed', closed_at: '2026-06-08T00:00:00Z' }),
      });
    });
    mockPost.mockResolvedValue({ data: makeAssignment({ status: 'active', closed_at: null }) });
    renderPage();
    fireEvent.click(await screen.findByTestId('reopen-button'));
    await waitFor(() => expect(mockPost).toHaveBeenCalledWith('/assignments/7/reopen/'));
  });

  it('disables due-date controls when assignment is closed', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('/submissions')) return Promise.resolve({ data: [] });
      return Promise.resolve({
        data: makeAssignment({ status: 'closed', closed_at: '2026-06-08T00:00:00Z' }),
      });
    });
    renderPage();
    const input = (await screen.findByTestId('due-at-input')) as HTMLInputElement;
    expect(input.disabled).toBe(true);
    expect((screen.getByTestId('due-at-save') as HTMLButtonElement).disabled).toBe(true);
  });
});
