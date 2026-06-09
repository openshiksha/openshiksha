import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProblemSetVersionsPage } from './ProblemSetVersionsPage';
import type {
  VersionDiffResponse,
  VersionSummary,
} from './useProblemSetVersions';

const mockVersions = vi.fn();
const mockDiff = vi.fn();

vi.mock('./useProblemSetVersions', () => ({
  useProblemSetVersions: (id: number | null) => mockVersions(id),
  useVersionDiff: (
    setId: number | null,
    targetId: number | null,
    againstId: number | null,
  ) => mockDiff(setId, targetId, againstId),
}));

const renderPage = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/teacher/problem-sets/9/versions']}>
        <Routes>
          <Route
            path="/teacher/problem-sets/:id/versions"
            element={<ProblemSetVersionsPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

const versions: VersionSummary[] = [
  {
    id: 2,
    version_number: 2,
    content_hash: 'abc',
    created_at: '2026-06-08T10:00:00Z',
    created_by_name: 'Tara',
    question_count: 3,
    assignment_count: 1,
  },
  {
    id: 1,
    version_number: 1,
    content_hash: 'xyz',
    created_at: '2026-06-07T10:00:00Z',
    created_by_name: 'Tara',
    question_count: 2,
    assignment_count: 4,
  },
];

const emptyDiffResponse: VersionDiffResponse = {
  target: { id: 2, version_number: 2 },
  against: { id: 1, version_number: 1 },
  diff: { questions_added: [], questions_removed: [], answer_changes: [], content_changes: [] },
};

describe('<ProblemSetVersionsPage />', () => {
  beforeEach(() => {
    mockVersions.mockReset();
    mockDiff.mockReset();
    mockDiff.mockReturnValue({ data: undefined, isLoading: false, isError: false });
  });

  it('lists every version row newest-first with summary info', () => {
    mockVersions.mockReturnValue({
      data: { problem_set_id: 9, versions },
      isLoading: false,
      isError: false,
    });
    renderPage();
    const rows = screen.getAllByTestId(/^version-row-/);
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveAttribute('data-testid', 'version-row-2');
    expect(rows[1]).toHaveAttribute('data-testid', 'version-row-1');
    expect(rows[0]).toHaveTextContent('v2');
    expect(rows[1]).toHaveTextContent('4 pinned assignments');
  });

  it('selects a target on first click and an against on second click', () => {
    mockVersions.mockReturnValue({
      data: { problem_set_id: 9, versions },
      isLoading: false,
      isError: false,
    });
    mockDiff.mockReturnValue({
      data: { ...emptyDiffResponse, diff: { ...emptyDiffResponse.diff, answer_changes: [{ subpart_id: 1, question_id: 1, before: {}, after: {} }] } },
      isLoading: false,
      isError: false,
    });
    renderPage();

    fireEvent.click(screen.getByTestId('version-row-2'));
    expect(screen.getByTestId('version-row-2')).toHaveAttribute('data-state', 'target');
    expect(screen.getByTestId('diff-helper-text')).toHaveTextContent(/another version/i);

    fireEvent.click(screen.getByTestId('version-row-1'));
    expect(screen.getByTestId('version-row-1')).toHaveAttribute('data-state', 'against');

    expect(screen.getByTestId('diff-panel')).toBeInTheDocument();
    expect(screen.getByTestId('diff-lines')).toHaveTextContent(/1 answer\(s\) changed/);
  });

  it('shows "Identical content" when the diff is empty', () => {
    mockVersions.mockReturnValue({
      data: { problem_set_id: 9, versions },
      isLoading: false,
      isError: false,
    });
    mockDiff.mockReturnValue({ data: emptyDiffResponse, isLoading: false, isError: false });
    renderPage();
    fireEvent.click(screen.getByTestId('version-row-2'));
    fireEvent.click(screen.getByTestId('version-row-1'));
    expect(screen.getByTestId('diff-no-changes')).toBeInTheDocument();
  });

  it('renders an empty state when the set has no versions', () => {
    mockVersions.mockReturnValue({
      data: { problem_set_id: 9, versions: [] },
      isLoading: false,
      isError: false,
    });
    renderPage();
    expect(screen.queryByTestId('version-list')).not.toBeInTheDocument();
    expect(screen.getByText(/No versions yet/i)).toBeInTheDocument();
  });
});
