import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EnrollStudentsModal } from './EnrollStudentsModal';
import type { SchoolPerson } from './useSchoolPeople';

const students: SchoolPerson[] = [
  { id: 1, full_name: 'Aarav Sharma', email: 'aarav@test.example' },
  { id: 2, full_name: 'Diya Patel', email: 'diya@test.example' },
  { id: 3, full_name: 'Rohan Gupta', email: 'rohan@test.example' },
];

const makeProps = (overrides = {}) => ({
  title: 'Roster — Grade 7-A',
  students,
  isPending: false,
  onAction: vi.fn().mockResolvedValue({ enrolled: [1], invalid_ids: [], student_count: 1 }),
  onClose: vi.fn(),
  ...overrides,
});

describe('EnrollStudentsModal', () => {
  it('renders all students and the title', () => {
    render(<EnrollStudentsModal {...makeProps()} />);
    expect(screen.getByText('Roster — Grade 7-A')).toBeDefined();
    expect(screen.getByText('Aarav Sharma')).toBeDefined();
    expect(screen.getByText('Diya Patel')).toBeDefined();
  });

  it('filters students by search query', () => {
    render(<EnrollStudentsModal {...makeProps()} />);
    fireEvent.change(screen.getByPlaceholderText(/search students/i), {
      target: { value: 'diya' },
    });
    expect(screen.getByText('Diya Patel')).toBeDefined();
    expect(screen.queryByText('Aarav Sharma')).toBeNull();
  });

  it('enroll/remove buttons are disabled until a student is selected', () => {
    render(<EnrollStudentsModal {...makeProps()} />);
    const enrollBtn = screen.getByRole('button', { name: 'Enroll' });
    expect(enrollBtn.hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.getByLabelText(/aarav sharma/i, { selector: 'input' }));
    expect(enrollBtn.hasAttribute('disabled')).toBe(false);
  });

  it('calls onAction with selected ids and "enroll"', async () => {
    const props = makeProps();
    render(<EnrollStudentsModal {...props} />);
    fireEvent.click(screen.getByLabelText(/aarav sharma/i, { selector: 'input' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enroll' }));
    await waitFor(() => expect(props.onAction).toHaveBeenCalledWith([1], 'enroll'));
  });

  it('reports skipped invalid ids in the result message', async () => {
    const props = makeProps({
      onAction: vi.fn().mockResolvedValue({ enrolled: [1], invalid_ids: [99], student_count: 1 }),
    });
    render(<EnrollStudentsModal {...props} />);
    fireEvent.click(screen.getByLabelText(/aarav sharma/i, { selector: 'input' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enroll' }));
    await waitFor(() => expect(screen.getByText(/1 skipped/i)).toBeDefined());
  });
});
