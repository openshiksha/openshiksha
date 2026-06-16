import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { I18nProvider } from '@/shared/i18n/I18nProvider';
import { AssignmentDetailPage } from './AssignmentDetailPage';

// MSO-9 — focused coverage of the offline final-submit flow. We mock the data +
// mutation hooks so we can drive connectivity and the queued mutation's eventual
// replay deterministically.

const existingSubmission = {
  id: 5,
  assignment: 1,
  answers: { '101': '42' },
  completion: 1,
  submitted_at: null,
  score: null,
};

const assignment = {
  id: 1,
  problem_set: {
    title: 'Polynomials Practice',
    subject: { name: 'Mathematics' },
    chapter: { id: 9, name: 'Polynomials' },
    questions: [{ id: 1, subparts: [{ id: 101 }] }],
  },
};

const patchMutate = vi.fn();

vi.mock('./useAssignmentDetail', () => ({
  useAssignmentDetail: () => ({ data: assignment, isLoading: false, error: null }),
}));

vi.mock('./useSubmission', () => ({
  useSubmission: () => ({ data: existingSubmission, isLoading: false }),
  useCreateSubmission: () => ({ mutate: vi.fn(), isPending: false }),
  usePatchSubmission: () => ({ mutate: patchMutate, isPending: false }),
}));

// SyncStatus and VideosPanel read React Query / network; stub them out — covered
// by their own tests.
vi.mock('./SyncStatus', () => ({ SyncStatus: () => null }));
vi.mock('./VideosPanel', () => ({ VideosPanel: () => null }));

vi.mock('./QuestionCard', () => ({
  QuestionCard: ({ isSubmitted }: { isSubmitted: boolean }) => (
    <div data-testid="qcard">{isSubmitted ? 'locked' : 'editable'}</div>
  ),
}));

const setOnLine = (value: boolean) =>
  Object.defineProperty(navigator, 'onLine', { configurable: true, value });

const renderPage = () =>
  render(
    <I18nProvider initialLocale="en">
      <MemoryRouter initialEntries={['/student/assignments/1']}>
        <Routes>
          <Route path="/student/assignments/:id" element={<AssignmentDetailPage />} />
        </Routes>
      </MemoryRouter>
    </I18nProvider>,
  );

beforeEach(() => {
  patchMutate.mockReset();
  setOnLine(true);
});
afterEach(() => {
  setOnLine(true);
  vi.restoreAllMocks();
});

describe('AssignmentDetailPage — offline final-submit (MSO-9)', () => {
  it('submits offline: optimistic "will be graded when back online" + locked inputs + queued mutation', async () => {
    const user = userEvent.setup();
    setOnLine(false);
    renderPage();

    expect(screen.getByTestId('qcard')).toHaveTextContent('editable');

    await user.click(screen.getByRole('button', { name: 'Submit assignment' }));
    // Confirm dialog → confirm.
    await user.click(screen.getByRole('button', { name: 'Submit' }));

    // Optimistic submitted view with the honest offline copy (no fake score).
    expect(screen.getByText(/will be graded when you're back online/i)).toBeInTheDocument();
    expect(screen.queryByText('%')).not.toBeInTheDocument();
    // Inputs are locked after submit.
    expect(screen.getByTestId('qcard')).toHaveTextContent('locked');
    // The submit mutation was queued with submitted_at set.
    expect(patchMutate).toHaveBeenCalledTimes(1);
    expect(patchMutate.mock.calls[0][0].data.submitted_at).toBeTruthy();
  });

  it('reconciles the real score when the queued submit replays on reconnect', async () => {
    const user = userEvent.setup();
    setOnLine(false);
    renderPage();

    await user.click(screen.getByRole('button', { name: 'Submit assignment' }));
    await user.click(screen.getByRole('button', { name: 'Submit' }));
    expect(screen.getByText(/will be graded when you're back online/i)).toBeInTheDocument();

    // Replay succeeds: invoke the onSuccess the component passed to mutate.
    const onSuccess = patchMutate.mock.calls[0][1].onSuccess as (s: { score: number }) => void;
    act(() => onSuccess({ score: 0.8 }));

    expect(screen.getByText('80%')).toBeInTheDocument();
    expect(
      screen.queryByText(/will be graded when you're back online/i),
    ).not.toBeInTheDocument();
  });

  it('re-opens the form if the queued submit ultimately fails', async () => {
    const user = userEvent.setup();
    setOnLine(false);
    renderPage();

    await user.click(screen.getByRole('button', { name: 'Submit assignment' }));
    await user.click(screen.getByRole('button', { name: 'Submit' }));
    expect(screen.getByTestId('qcard')).toHaveTextContent('locked');

    const onError = patchMutate.mock.calls[0][1].onError as () => void;
    act(() => onError());

    // Back to an editable, submittable form.
    expect(screen.getByTestId('qcard')).toHaveTextContent('editable');
    expect(screen.queryByText(/will be graded when you're back online/i)).not.toBeInTheDocument();
  });
});
