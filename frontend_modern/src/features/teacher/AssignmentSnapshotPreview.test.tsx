import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { AssignmentSnapshotPreview } from './AssignmentSnapshotPreview';
import type { ProblemSetWithQuestions } from '@/types/index';

vi.mock('../student/QuestionCard', () => ({
  QuestionCard: ({ question }: { question: { id: number; subparts: { question_text: string }[] } }) => (
    <div data-testid={`qcard-${question.id}`}>{question.subparts[0]?.question_text ?? ''}</div>
  ),
}));

const mockUndo = vi.fn();
vi.mock('./useAssignmentResync', () => ({
  useUndoResync: () => ({ mutate: mockUndo, isPending: false }),
  useResyncPreview: () => ({ data: undefined, isLoading: false, isError: false }),
  useApplyResync: () => ({ mutateAsync: vi.fn(), isPending: false, isError: false }),
}));

// ResyncAssignmentModal does its own preview fetching; keep this test focused
// on the surface that mounts it. We don't need its real internals.
vi.mock('./ResyncAssignmentModal', () => ({
  ResyncAssignmentModal: ({ open }: { open: boolean }) =>
    open ? <div data-testid="resync-modal" /> : null,
}));

const renderPreview = (
  overrides: Partial<{ drift: boolean; hasResyncHistory: boolean; locale: 'en' | 'hi' }> & {
    questions?: unknown[];
  } = {},
) => {
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
  const locale = overrides.locale ?? 'en';
  return render(
    <I18nProvider initialLocale={locale}>
      <MemoryRouter>
        <AssignmentSnapshotPreview
          assignmentId={7}
          problemSet={problemSet}
          snapshotDrift={overrides.drift ?? false}
          hasResyncHistory={overrides.hasResyncHistory ?? false}
        />
      </MemoryRouter>
    </I18nProvider>,
  );
};

describe('<AssignmentSnapshotPreview />', () => {
  it('starts collapsed and reveals the question cards on toggle', () => {
    renderPreview();
    expect(screen.queryByTestId('qcard-101')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('snapshot-toggle'));
    expect(screen.getByTestId('qcard-101')).toBeInTheDocument();
    expect(screen.getByText('Frozen prompt')).toBeInTheDocument();
  });

  it('does not render the drift banner when the snapshot matches the live set', () => {
    renderPreview({ drift: false });
    expect(screen.queryByTestId('snapshot-drift-banner')).not.toBeInTheDocument();
    expect(screen.queryByTestId('open-resync-modal')).not.toBeInTheDocument();
  });

  it('renders the drift banner with a link to the live preview when drift is true', () => {
    renderPreview({ drift: true });
    const banner = screen.getByTestId('snapshot-drift-banner');
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/live set has changed/i);
    const link = screen.getByRole('link', { name: /compare with the live set/i });
    expect(link).toHaveAttribute('href', '/teacher/problem-sets/9/preview');
  });

  it('opens the resync modal when the drift-banner action is clicked', () => {
    renderPreview({ drift: true });
    expect(screen.queryByTestId('resync-modal')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('open-resync-modal'));
    expect(screen.getByTestId('resync-modal')).toBeInTheDocument();
  });

  it('renders the undo bar when there is prior resync history and calls the mutation', () => {
    mockUndo.mockReset();
    renderPreview({ hasResyncHistory: true });
    expect(screen.getByTestId('undo-resync-bar')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('undo-resync'));
    expect(mockUndo).toHaveBeenCalled();
  });

  it('does not render the undo bar when there is no resync history', () => {
    renderPreview({ hasResyncHistory: false });
    expect(screen.queryByTestId('undo-resync-bar')).not.toBeInTheDocument();
  });

  it('renders an empty-state message when the snapshot has no questions', () => {
    renderPreview({ questions: [] });
    fireEvent.click(screen.getByTestId('snapshot-toggle'));
    expect(screen.getByText(/snapshot is empty/i)).toBeInTheDocument();
  });

  it('renders the drift banner in Hindi when the locale is हिं', async () => {
    renderPreview({ drift: true, locale: 'hi' });
    // लाइव सेट = "live set" per the Glossary register.
    await waitFor(() => {
      expect(screen.getByTestId('snapshot-drift-banner')).toHaveTextContent(/लाइव सेट/);
    });
  });
});
