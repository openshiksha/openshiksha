import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ResyncAssignmentModal } from './ResyncAssignmentModal';
import type { ResyncPreview } from './useAssignmentResync';

const mockPreview = vi.fn();
const mockApplyAsync = vi.fn();
const mockApply = vi.fn();

vi.mock('./useAssignmentResync', () => ({
  useResyncPreview: () => mockPreview(),
  useApplyResync: () => mockApply(),
}));

const baseDiff: ResyncPreview['diff'] = {
  questions_added: [],
  questions_removed: [],
  answer_changes: [],
  content_changes: [],
};

const drift = (overrides: Partial<ResyncPreview>): ResyncPreview => ({
  assignment_id: 7,
  has_drift: true,
  diff: { ...baseDiff, ...(overrides.diff ?? {}) },
  affected: {
    submitted_count: 0,
    graded_count: 0,
    regrade_on_apply: 0,
    ...(overrides.affected ?? {}),
  },
});

describe('<ResyncAssignmentModal />', () => {
  beforeEach(() => {
    mockApplyAsync.mockReset();
    mockApplyAsync.mockResolvedValue({});
    mockApply.mockReturnValue({ mutateAsync: mockApplyAsync, isPending: false, isError: false });
  });

  it('renders nothing when closed', () => {
    mockPreview.mockReturnValue({ data: undefined, isLoading: false, isError: false });
    const { container } = render(
      <ResyncAssignmentModal assignmentId={7} open={false} onClose={() => {}} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('shows a loading state while the preview is in flight', () => {
    mockPreview.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    render(<ResyncAssignmentModal assignmentId={7} open onClose={() => {}} />);
    // The apply button is rendered but disabled while loading.
    expect(screen.getByTestId('resync-apply')).toBeDisabled();
  });

  it('disables Apply when there is no drift', () => {
    mockPreview.mockReturnValue({
      data: { ...drift({}), has_drift: false },
      isLoading: false,
      isError: false,
    });
    render(<ResyncAssignmentModal assignmentId={7} open onClose={() => {}} />);
    expect(screen.getByText(/already matches the live set/i)).toBeInTheDocument();
    expect(screen.getByTestId('resync-apply')).toBeDisabled();
  });

  it('shows the diff summary lines and the answer-change warning', () => {
    mockPreview.mockReturnValue({
      data: drift({
        diff: {
          ...baseDiff,
          questions_added: [11],
          answer_changes: [{ subpart_id: 1, question_id: 11, before: {}, after: {} }],
        },
        affected: { submitted_count: 5, graded_count: 3, regrade_on_apply: 3 },
      }),
      isLoading: false,
      isError: false,
    });
    render(<ResyncAssignmentModal assignmentId={7} open onClose={() => {}} />);
    const summary = screen.getByTestId('resync-diff-summary');
    expect(summary).toHaveTextContent(/1 question added/i);
    expect(summary).toHaveTextContent(/1 answer changed/i);
    expect(screen.getByTestId('resync-regrade-note')).toHaveTextContent(/3 graded submissions/i);
    expect(screen.getByTestId('resync-apply')).toHaveTextContent(/Update and re-grade 3/);
  });

  it('calls the apply mutation and closes when confirmed', async () => {
    mockPreview.mockReturnValue({
      data: drift({ diff: { ...baseDiff, content_changes: [{ subpart_id: 1, question_id: 1 }] } }),
      isLoading: false,
      isError: false,
    });
    const onClose = vi.fn();
    const onApplied = vi.fn();
    render(
      <ResyncAssignmentModal assignmentId={7} open onClose={onClose} onApplied={onApplied} />,
    );

    fireEvent.click(screen.getByTestId('resync-apply'));
    await vi.waitFor(() => expect(mockApplyAsync).toHaveBeenCalledTimes(1));
    expect(onApplied).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });
});
