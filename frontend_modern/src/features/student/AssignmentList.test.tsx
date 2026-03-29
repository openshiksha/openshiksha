import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AssignmentList } from './AssignmentList';
import type { Assignment } from '@/types/index';
import { addDays, subDays, formatISO } from 'date-fns';

function makeAssignment(overrides: Partial<Assignment> = {}): Assignment {
  return {
    id: Math.floor(Math.random() * 10000),
    subject_room: 1,
    subject_room_display: 'Mathematics - Class 10A',
    problem_set: {
      id: 1,
      title: 'Chapter 3 Practice Set',
      description: '',
      chapter: { id: 1, name: 'Quadratic Equations' },
      subject: { id: 1, name: 'Mathematics' },
      standard: { id: 1, name: 'Class 10' },
      question_count: 10,
      estimated_minutes: 30,
      is_active: true,
    },
    assigned_by: 1,
    assigned_at: formatISO(new Date()),
    due_at: formatISO(addDays(new Date(), 5)),
    number: 1,
    average_score: null,
    completion_rate: null,
    my_submission: null,
    ...overrides,
  };
}

describe('AssignmentList', () => {
  it('shows empty state when there are no assignments', () => {
    render(<AssignmentList assignments={[]} />);
    expect(screen.getByText(/no assignments yet/i)).toBeDefined();
  });

  it('shows upcoming section for future assignments', () => {
    const assignment = makeAssignment({ due_at: formatISO(addDays(new Date(), 7)) });
    render(<AssignmentList assignments={[assignment]} />);
    expect(screen.getByText(/upcoming/i)).toBeDefined();
    expect(screen.getByText('Chapter 3 Practice Set')).toBeDefined();
  });

  it('shows overdue section for past-due assignments without submission', () => {
    const assignment = makeAssignment({ due_at: formatISO(subDays(new Date(), 2)) });
    render(<AssignmentList assignments={[assignment]} />);
    expect(screen.getByText(/overdue/i)).toBeDefined();
  });

  it('shows completed section for submitted assignments', () => {
    const assignment = makeAssignment({
      my_submission: {
        id: 1,
        assignment: 1,
        student: 1,
        score: 0.85,
        completion: 1.0,
        answers: {},
        submitted_at: formatISO(subDays(new Date(), 1)),
        is_revised: false,
        created_at: formatISO(subDays(new Date(), 2)),
        updated_at: formatISO(subDays(new Date(), 1)),
      },
    });
    render(<AssignmentList assignments={[assignment]} />);
    expect(screen.getByText(/completed/i)).toBeDefined();
  });

  it('shows due soon section for assignments due within 3 days', () => {
    const assignment = makeAssignment({ due_at: formatISO(addDays(new Date(), 2)) });
    render(<AssignmentList assignments={[assignment]} />);
    expect(screen.getByText(/due soon/i)).toBeDefined();
  });

  it('correctly categorizes multiple assignments into separate sections', () => {
    const assignments = [
      makeAssignment({ id: 1, due_at: formatISO(subDays(new Date(), 1)) }), // overdue
      makeAssignment({ id: 2, due_at: formatISO(addDays(new Date(), 2)) }), // due soon
      makeAssignment({ id: 3, due_at: formatISO(addDays(new Date(), 7)) }), // upcoming
    ];
    render(<AssignmentList assignments={assignments} />);
    expect(screen.getByText(/overdue/i)).toBeDefined();
    expect(screen.getByText(/due soon/i)).toBeDefined();
    expect(screen.getByText(/upcoming/i)).toBeDefined();
  });
});
