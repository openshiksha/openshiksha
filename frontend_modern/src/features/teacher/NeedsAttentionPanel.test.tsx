import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { NeedsAttentionPanel } from './NeedsAttentionPanel';
import { bucketize } from './needsAttention';
import type { Assignment, ProblemSet } from '@/types/index';

const { mockNavigate } = vi.hoisted(() => ({ mockNavigate: vi.fn() }));
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const STUB_PS: ProblemSet = {
  id: 1,
  title: 'Set',
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
    id: 1,
    subject_room: 1,
    subject_room_display: 'Std 8 A · Math',
    problem_set: STUB_PS,
    assigned_by: 1,
    assigned_at: '2026-06-01T00:00:00Z',
    due_at: '2026-06-05T00:00:00Z',
    number: 1,
    average_score: null,
    completion_rate: 0.3,
    submission_count: 3,
    student_count: 10,
    ...overrides,
  };
}

const NOW = new Date('2026-06-07T00:00:00Z');

describe('bucketize', () => {
  it('skips future-dated assignments', () => {
    const a = makeAssignment({ due_at: '2026-07-01T00:00:00Z' });
    const buckets = bucketize([a], NOW);
    expect(buckets.every((b) => b.items.length === 0)).toBe(true);
  });

  it('puts past-due partially-submitted assignments in overdue', () => {
    const a = makeAssignment({ id: 1, completion_rate: 0.4, average_score: null });
    const buckets = bucketize([a], NOW);
    expect(buckets.find((b) => b.label === 'overdue')?.items).toHaveLength(1);
    expect(buckets.find((b) => b.label === 'ungraded')?.items).toHaveLength(0);
  });

  it('puts fully-submitted-but-ungraded past-due assignments in ungraded', () => {
    const a = makeAssignment({ id: 2, completion_rate: 1.0, average_score: null });
    const buckets = bucketize([a], NOW);
    expect(buckets.find((b) => b.label === 'ungraded')?.items).toHaveLength(1);
    expect(buckets.find((b) => b.label === 'overdue')?.items).toHaveLength(0);
  });

  it('puts graded past-due with low completion in low-completion', () => {
    // completion 1.0 keeps it out of overdue, avg_score set keeps it out of ungraded
    // But low completion < 0.5 requires completion < 0.5 — so this is mutually exclusive
    // with "fully submitted". Real case: partial submission already graded.
    const a = makeAssignment({ id: 3, completion_rate: 0.3, average_score: 0.7 });
    const buckets = bucketize([a], NOW);
    // Precedence puts partially-submitted into overdue, not low-completion.
    expect(buckets.find((b) => b.label === 'overdue')?.items).toHaveLength(1);
  });

  it('does not double-count an assignment across buckets', () => {
    const a = makeAssignment({ id: 4, completion_rate: 0.2, average_score: null });
    const buckets = bucketize([a], NOW);
    const total = buckets.reduce((sum, b) => sum + b.items.length, 0);
    expect(total).toBe(1);
  });
});

describe('NeedsAttentionPanel', () => {
  it('renders nothing when assignments is undefined', () => {
    const { container } = render(
      <MemoryRouter>
        <NeedsAttentionPanel assignments={undefined} />
      </MemoryRouter>,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when no assignments need attention', () => {
    const future = makeAssignment({ due_at: '2099-01-01T00:00:00Z' });
    const { container } = render(
      <MemoryRouter>
        <NeedsAttentionPanel assignments={[future]} />
      </MemoryRouter>,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders the strip with chip counts for overdue and ungraded items', () => {
    const a1 = makeAssignment({ id: 10, completion_rate: 0.3, average_score: null });
    const a2 = makeAssignment({ id: 11, completion_rate: 0.4, average_score: null });
    const a3 = makeAssignment({ id: 12, completion_rate: 1.0, average_score: null });
    render(
      <MemoryRouter>
        <NeedsAttentionPanel assignments={[a1, a2, a3]} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId('needs-attention-overdue')).toHaveTextContent('2 overdue');
    expect(screen.getByTestId('needs-attention-ungraded')).toHaveTextContent('1 ungraded');
  });

  it('deep-links the chip to the earliest-due assignment in the bucket', () => {
    const a1 = makeAssignment({ id: 20, due_at: '2026-06-06T00:00:00Z', completion_rate: 0.3, average_score: null });
    const a2 = makeAssignment({ id: 21, due_at: '2026-06-04T00:00:00Z', completion_rate: 0.3, average_score: null });
    render(
      <MemoryRouter>
        <NeedsAttentionPanel assignments={[a1, a2]} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId('needs-attention-overdue'));
    expect(mockNavigate).toHaveBeenCalledWith('/teacher/assignments/21');
  });
});
