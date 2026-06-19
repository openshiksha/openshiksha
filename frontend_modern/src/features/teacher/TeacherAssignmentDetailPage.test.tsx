import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { TeacherAssignmentDetailPage } from './TeacherAssignmentDetailPage';
import type { SubmissionWithStudent } from './useTeacherAssignmentDetail';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ id: '7' }), useNavigate: () => vi.fn() };
});

// Keep the snapshot preview (its own fetching) out of this layout-focused test.
vi.mock('./AssignmentSnapshotPreview', () => ({
  AssignmentSnapshotPreview: () => <div data-testid="snapshot-preview" />,
}));

const mockMeta = {
  data: {
    id: 7,
    subject_room: 3,
    subject_room_display: 'Math · 9A',
    problem_set: { id: 9, title: 'Algebra Set' },
    due_at: '2026-06-20T10:00:00Z',
    student_count: 3,
    average_score: 0.72,
    snapshot_drift: false,
    has_resync_history: false,
  },
  isLoading: false,
  isError: false,
};

let mockSubmissions: SubmissionWithStudent[] = [];

vi.mock('./useTeacherAssignmentDetail', () => ({
  useTeacherAssignmentDetail: () => ({
    metaQuery: mockMeta,
    submissionsQuery: { data: mockSubmissions, isLoading: false, isError: false },
  }),
}));

vi.mock('./useQuestionMistakes', () => ({
  useQuestionMistakes: () => ({ data: [] }),
}));

const renderPage = (locale: 'en' | 'hi' = 'en') =>
  render(
    <I18nProvider initialLocale={locale}>
      <MemoryRouter>
        <TeacherAssignmentDetailPage />
      </MemoryRouter>
    </I18nProvider>,
  );

const sub = (over: Partial<SubmissionWithStudent>): SubmissionWithStudent =>
  ({
    id: 1,
    student_name: 'Asha',
    submitted_at: '2026-06-19T09:00:00Z',
    score: 0.8,
    ...over,
  }) as SubmissionWithStudent;

describe('<TeacherAssignmentDetailPage /> submissions', () => {
  it('renders submissions as both a table and a mobile card list', () => {
    mockSubmissions = [sub({ id: 1, student_name: 'Asha' }), sub({ id: 2, student_name: 'Ravi' })];
    const { container } = renderPage();

    const table = container.querySelector('table');
    expect(table).not.toBeNull();
    expect(table?.className).toContain('sm:table');
    expect(within(table!).getByText('Asha')).toBeInTheDocument();

    const list = container.querySelector('ul.sm\\:hidden');
    expect(list).not.toBeNull();
    expect(list?.querySelectorAll('li')).toHaveLength(2);
  });

  it('renders the right status badge for graded vs pending submissions', () => {
    mockSubmissions = [
      sub({ id: 1, submitted_at: '2026-06-19T09:00:00Z', score: 0.8 }),
      sub({ id: 2, submitted_at: null, score: null }),
    ];
    renderPage();
    // Each appears twice (table + card); just assert presence.
    expect(screen.getAllByText(/Submitted/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Pending/).length).toBeGreaterThan(0);
  });

  it('shows the empty state when there are no submissions', () => {
    mockSubmissions = [];
    renderPage();
    expect(screen.getByText('No submissions yet.')).toBeInTheDocument();
  });

  it('localizes page strings in Hindi', async () => {
    mockSubmissions = [sub({ id: 1 })];
    renderPage('hi');
    // The hi dictionary loads via a dynamic import, so await its appearance.
    expect(await screen.findByText('छात्रों के सबमिशन')).toBeInTheDocument();
  });
});
