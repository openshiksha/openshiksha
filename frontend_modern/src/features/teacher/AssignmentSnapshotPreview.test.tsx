import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { AssignmentSnapshotPreview } from './AssignmentSnapshotPreview';
import type { ProblemSetWithQuestions } from '@/types/index';

vi.mock('../student/QuestionCard', () => ({
  QuestionCard: ({ question }: { question: { id: number; subparts: { question_text: string }[] } }) => (
    <div data-testid={`qcard-${question.id}`}>{question.subparts[0]?.question_text ?? ''}</div>
  ),
}));

const renderPreview = (overrides: Partial<{ drift: boolean }> & { questions?: unknown[] } = {}) => {
  const problemSet = {
    id: 9,
    title: 'Algebra',
    description: '',
    chapter: { id: 1, name: 'Algebra' },
    subject: { id: 1, name: 'Math' },
    standard: { id: 1, name: '9' },
    question_count: 1,
    estimated_minutes: null,
    is_active: true,
    is_remedial: false,
    source_assignment: null,
    questions: overrides.questions ?? [{ id: 101, subparts: [{ question_text: 'Frozen prompt' }] }],
  } as unknown as ProblemSetWithQuestions;
  return render(
    <MemoryRouter>
      <AssignmentSnapshotPreview
        problemSet={problemSet}
        snapshotDrift={overrides.drift ?? false}
      />
    </MemoryRouter>,
  );
};

describe('<AssignmentSnapshotPreview />', () => {
  it('starts collapsed and reveals the question cards on toggle', () => {
    renderPreview();
    // Collapsed: no question card rendered yet.
    expect(screen.queryByTestId('qcard-101')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('snapshot-toggle'));
    expect(screen.getByTestId('qcard-101')).toBeInTheDocument();
    expect(screen.getByText('Frozen prompt')).toBeInTheDocument();
  });

  it('does not render the drift banner when the snapshot matches the live set', () => {
    renderPreview({ drift: false });
    expect(screen.queryByTestId('snapshot-drift-banner')).not.toBeInTheDocument();
  });

  it('renders the drift banner with a link to the live preview when drift is true', () => {
    renderPreview({ drift: true });
    const banner = screen.getByTestId('snapshot-drift-banner');
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/live set has changed/i);
    const link = screen.getByRole('link', { name: /compare with the live set/i });
    expect(link).toHaveAttribute('href', '/teacher/problem-sets/9/preview');
  });

  it('renders an empty-state message when the snapshot has no questions', () => {
    renderPreview({ questions: [] });
    fireEvent.click(screen.getByTestId('snapshot-toggle'));
    expect(screen.getByText(/snapshot is empty/i)).toBeInTheDocument();
  });
});
