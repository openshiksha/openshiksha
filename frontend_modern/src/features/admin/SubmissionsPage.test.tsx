import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import { SubmissionsPage } from './SubmissionsPage';
import { packQuestionToPreview } from './submissionPreview';
import type {
  ContentSubmissionDetail,
  ContentSubmissionSummary,
  PackQuestion,
} from './useContentSubmissions';

// Mock the hooks module so the page tests need no QueryClientProvider and can
// drive mutation callbacks synchronously (the DTB-3 precedent).
const { mockUseList, mockUseDetail, mockMutate, mockUseTransition } = vi.hoisted(() => {
  const mockMutate = vi.fn();
  return {
    mockMutate,
    mockUseList: vi.fn(),
    mockUseDetail: vi.fn(),
    mockUseTransition: vi.fn(() => ({ mutate: mockMutate, isPending: false })),
  };
});

vi.mock('./useContentSubmissions', () => ({
  useContentSubmissions: mockUseList,
  useContentSubmission: mockUseDetail,
  useSubmissionTransition: mockUseTransition,
}));

const summary: ContentSubmissionSummary = {
  id: 7,
  name: 'Fractions pack',
  pack_hash: 'abc123def456abc123def456',
  provenance: { author: 'Asha Kulkarni', license: 'CC-BY-4.0', source: 'https://example.org' },
  state: 'pending',
  state_display: 'Pending review',
  note: '',
  reviewer_username: null,
  question_count: 1,
  created_at: '2026-07-07T00:00:00Z',
  updated_at: '2026-07-07T00:00:00Z',
  reviewed_at: null,
};

const packQuestion: PackQuestion = {
  standard: 5,
  subject: 'Mathematics',
  chapter: 'Fractions',
  question_type: 'numeric',
  difficulty: 2,
  subparts: [
    {
      index: 0,
      subpart_type: 'numeric',
      question_text: 'Mark one half on the number line.',
      options: null,
      correct_answer: { answer: 0.5 },
      widget_kind: 'number-line',
      widget_config: { min: 0, max: 1, step: 0.5 },
    },
  ],
};

const detail: ContentSubmissionDetail = {
  ...summary,
  payload: {
    pack_version: '1.0',
    provenance: summary.provenance,
    questions: [packQuestion],
  },
};

beforeEach(() => {
  mockMutate.mockReset();
  mockUseList.mockReset();
  mockUseDetail.mockReset();
  mockUseList.mockReturnValue({ data: [summary], isLoading: false });
  mockUseDetail.mockReturnValue({ data: detail, isLoading: false });
});

describe('<SubmissionsPage />', () => {
  it('defaults to the pending filter and renders queue rows', () => {
    render(<SubmissionsPage />);
    expect(mockUseList).toHaveBeenCalledWith('pending');
    expect(screen.getByText('Fractions pack')).toBeInTheDocument();
    expect(screen.getByText(/Asha Kulkarni · 1 question/)).toBeInTheDocument();
    expect(screen.getByText('Pending review')).toBeInTheDocument();
  });

  it('shows the empty state when no submissions match', () => {
    mockUseList.mockReturnValue({ data: [], isLoading: false });
    render(<SubmissionsPage />);
    expect(screen.getByText('No submissions')).toBeInTheDocument();
  });

  it('switching the state filter re-queries and clears the selection', () => {
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Approved' }));
    expect(mockUseList).toHaveBeenLastCalledWith('approved');
  });

  it('selecting a row shows provenance, the question preview, and the sandboxed widget preview', () => {
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));

    // Provenance block — the attribution the approval publishes with.
    expect(screen.getByText('CC-BY-4.0')).toBeInTheDocument();
    expect(screen.getByText('https://example.org')).toBeInTheDocument();
    // The real question preview (same panel teachers use).
    expect(screen.getByText('Mark one half on the number line.')).toBeInTheDocument();
    // The real sandboxed widget preview, labeled with its kind.
    expect(screen.getByText(/Widget preview \(sandboxed\) — number-line/)).toBeInTheDocument();
    expect(screen.getByTitle('Interactive question widget')).toBeInTheDocument();
  });

  it('approve calls the transition mutation without requiring a note', () => {
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));
    fireEvent.click(screen.getByRole('button', { name: 'Approve & publish to bank' }));

    expect(mockMutate).toHaveBeenCalledWith(
      { id: 7, action: 'approve', note: undefined },
      expect.anything(),
    );
  });

  it('reject without a note blocks locally and never calls the API', () => {
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));

    expect(mockMutate).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/note explaining the rejection/i);
  });

  it('reject with a note calls the transition mutation with it', () => {
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));
    fireEvent.change(screen.getByLabelText(/Review note/), {
      target: { value: 'Answers to Q2 are wrong.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Reject' }));

    expect(mockMutate).toHaveBeenCalledWith(
      { id: 7, action: 'reject', note: 'Answers to Q2 are wrong.' },
      expect.anything(),
    );
  });

  it('surfaces a server 409 from the state machine instead of papering over it', () => {
    mockMutate.mockImplementation((_input, opts) =>
      opts?.onError?.({ response: { data: { detail: 'Cannot approve from rejected.' } } }),
    );
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));
    fireEvent.click(screen.getByRole('button', { name: 'Approve & publish to bank' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Cannot approve from rejected.');
  });

  it('a rejected submission offers Reopen and drives the reopen transition', () => {
    mockUseDetail.mockReturnValue({
      data: {
        ...detail,
        state: 'rejected',
        state_display: 'Rejected',
        note: 'Bad answers.',
        reviewer_username: 'admin1',
        reviewed_at: '2026-07-07T01:00:00Z',
      },
      isLoading: false,
    });
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));

    expect(screen.getByText(/Reviewed by/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reopen' }));
    expect(mockMutate).toHaveBeenCalledWith(
      { id: 7, action: 'reopen', note: undefined },
      expect.anything(),
    );
  });

  it('an approved submission is read-only (no approve/reject buttons)', () => {
    mockUseDetail.mockReturnValue({
      data: { ...detail, state: 'approved', state_display: 'Approved' },
      isLoading: false,
    });
    render(<SubmissionsPage />);
    fireEvent.click(screen.getByText('Fractions pack'));

    expect(screen.getByText(/live in the shared bank/)).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Approve & publish to bank' }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Reject' })).not.toBeInTheDocument();
  });
});

describe('packQuestionToPreview', () => {
  it('maps a pack question onto the Question shape the preview panel renders', () => {
    const mapped = packQuestionToPreview(packQuestion, 0);
    expect(mapped.subject_name).toBe('Mathematics');
    expect(mapped.chapter_name).toBe('Fractions');
    expect(mapped.question_type).toBe('numeric');
    expect(mapped.subparts).toHaveLength(1);
    expect(mapped.subparts[0].question_text).toBe('Mark one half on the number line.');
    expect(mapped.subparts[0].is_interactive).toBe(true);
    expect(mapped.subparts[0].widget_kind).toBe('number-line');
  });

  it('applies the import defaults (mcq, difficulty 2) when the pack omits them', () => {
    const bare: PackQuestion = {
      standard: 3,
      subject: 'Science',
      chapter: 'Plants',
      subparts: [{ index: 0, question_text: 'Name one part of a plant.' }],
    };
    const mapped = packQuestionToPreview(bare, 1);
    expect(mapped.question_type).toBe('mcq');
    expect(mapped.difficulty).toBe(2);
    expect(mapped.subparts[0].is_interactive).toBe(false);
  });
});
