import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ProblemSetPreviewPage } from './ProblemSetPreviewPage';

const mockPreview = vi.fn();
const mockRemove = vi.fn();
const mockMutate = vi.fn();

vi.mock('./useProblemSetPreview', () => ({
  useProblemSetPreview: (id: number | null) => mockPreview(id),
}));

vi.mock('./useRemoveQuestionFromProblemSet', () => ({
  useRemoveQuestionFromProblemSet: () => mockRemove(),
}));

vi.mock('../student/QuestionCard', () => ({
  QuestionCard: ({ question }: { question: { id: number; subparts: { question_text: string }[] } }) => (
    <div data-testid={`qcard-${question.id}`}>{question.subparts[0]?.question_text ?? ''}</div>
  ),
}));

const renderAt = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/teacher/problem-sets/7/preview']}>
        <Routes>
          <Route
            path="/teacher/problem-sets/:id/preview"
            element={<ProblemSetPreviewPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const baseData = {
  id: 7,
  title: 'Algebra Set',
  description: '',
  number: 1,
  subject_name: 'Math',
  chapter_name: 'Algebra',
  estimated_minutes: null,
  question_count: 2,
  questions: [
    { id: 101, subparts: [{ question_text: 'Q1' }] },
    { id: 102, subparts: [{ question_text: 'Q2' }] },
  ],
};

describe('<ProblemSetPreviewPage />', () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockRemove.mockReturnValue({ mutate: mockMutate, isPending: false });
    window.confirm = vi.fn(() => true);
  });

  it('renders read-only preview by default and hides Edit set when not creator', () => {
    mockPreview.mockReturnValue({
      data: { ...baseData, created_by_me: false, assigned_count: 0, has_graded_submissions: false },
      isLoading: false,
      isError: false,
    });
    renderAt();
    expect(screen.getByText(/Student preview · read-only/i)).toBeInTheDocument();
    expect(screen.queryByTestId('toggle-edit')).not.toBeInTheDocument();
    expect(screen.queryByTestId('remove-101')).not.toBeInTheDocument();
  });

  it('shows the Edit set toggle when the current teacher is the creator', () => {
    mockPreview.mockReturnValue({
      data: { ...baseData, created_by_me: true, assigned_count: 0, has_graded_submissions: false },
      isLoading: false,
      isError: false,
    });
    renderAt();
    expect(screen.getByTestId('toggle-edit')).toBeInTheDocument();
  });

  it('reveals remove buttons in edit mode and calls the mutation', () => {
    mockPreview.mockReturnValue({
      data: { ...baseData, created_by_me: true, assigned_count: 0, has_graded_submissions: false },
      isLoading: false,
      isError: false,
    });
    renderAt();

    fireEvent.click(screen.getByTestId('toggle-edit'));
    expect(screen.getByText(/Editing set · live changes/i)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('remove-101'));
    expect(mockMutate).toHaveBeenCalledWith({ problemSetId: 7, questionId: 101 });
  });

  it('renders the AIV-3b safety banner in edit mode when the set is already assigned', () => {
    mockPreview.mockReturnValue({
      data: { ...baseData, created_by_me: true, assigned_count: 3, has_graded_submissions: true },
      isLoading: false,
      isError: false,
    });
    renderAt();
    fireEvent.click(screen.getByTestId('toggle-edit'));
    expect(screen.getByTestId('edit-safety-banner')).toBeInTheDocument();
    expect(screen.getByText(/used in 3 assignments\./i)).toBeInTheDocument();
    expect(screen.getByText(/graded against/i)).toBeInTheDocument();
  });

  it('does not call the mutation when the confirm dialog is dismissed', () => {
    mockPreview.mockReturnValue({
      data: { ...baseData, created_by_me: true, assigned_count: 0, has_graded_submissions: false },
      isLoading: false,
      isError: false,
    });
    window.confirm = vi.fn(() => false);

    renderAt();
    fireEvent.click(screen.getByTestId('toggle-edit'));
    fireEvent.click(screen.getByTestId('remove-101'));
    expect(mockMutate).not.toHaveBeenCalled();
  });
});
