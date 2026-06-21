import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { QuestionBankPage } from './QuestionBankPage';
import type { Question, Subject, ChapterItem } from '@/types/index';

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));
vi.mock('@/api/client', () => ({ apiClient: { get: mockGet, post: vi.fn() } }));

const SUBJECTS: Subject[] = [
  { id: 1, name: 'Mathematics', description: '' },
  { id: 2, name: 'Physics', description: '' },
];

const CHAPTERS: ChapterItem[] = [
  { id: 10, name: 'Algebra', standard_number: 8 } as ChapterItem,
  { id: 11, name: 'Geometry', standard_number: 8 } as ChapterItem,
];

function makeQuestion(overrides: Partial<Question> = {}): Question {
  return {
    id: 100,
    question_type: 'mcq',
    difficulty: 3,
    subject: 1,
    subject_name: 'Mathematics',
    chapter: 10,
    chapter_name: 'Algebra',
    standard: 8,
    tags: [],
    subparts: [{ id: 1, question_text: 'What is 2 + 2?', options: [], image_url: null }],
    created_by: 1,
    created_at: '2026-01-01',
    ...overrides,
  } as unknown as Question;
}

function LocationProbe() {
  const location = useLocation();
  return (
    <span data-testid="location">{location.pathname}{location.search}</span>
  );
}

function renderBank(initialEntry = '/teacher/questions') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route
            path="/teacher/questions"
            element={
              <>
                <QuestionBankPage />
                <LocationProbe />
              </>
            }
          />
          <Route path="*" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  mockGet.mockReset();
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/subjects')) return Promise.resolve({ data: SUBJECTS });
    if (url.startsWith('/chapters')) return Promise.resolve({ data: CHAPTERS });
    if (url.startsWith('/questions')) {
      return Promise.resolve({ data: { results: [makeQuestion()], count: 1 } });
    }
    return Promise.resolve({ data: [] });
  });
});

describe('QuestionBankPage — URL-driven filters & continuity', () => {
  it('renders the page title in Hindi when the locale is हिं', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <I18nProvider initialLocale="hi">
          <MemoryRouter initialEntries={['/teacher/questions']}>
            <Routes>
              <Route path="/teacher/questions" element={<QuestionBankPage />} />
            </Routes>
          </MemoryRouter>
        </I18nProvider>
      </QueryClientProvider>,
    );
    // प्रश्न बैंक = "question bank" per the Glossary register.
    await waitFor(() => {
      expect(screen.getByText('प्रश्न बैंक')).toBeInTheDocument();
    });
  });

  it('reads filters from the URL on first render', async () => {
    renderBank('/teacher/questions?q=2+2&subject=1&diff=3');
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/search question text/i) as HTMLInputElement;
      expect(searchInput.value).toBe('2 2');
    });
    // The questions API call should carry the filters
    await waitFor(() => {
      const calls = mockGet.mock.calls.map((c) => c[0] as string);
      expect(calls.some((u) => u.includes('/questions/') && u.includes('subject=1') && u.includes('difficulty=3'))).toBe(true);
    });
  });

  it('pushes search edits into the URL', async () => {
    renderBank('/teacher/questions');
    await screen.findByPlaceholderText(/search question text/i);
    const searchInput = screen.getByPlaceholderText(/search question text/i);
    fireEvent.change(searchInput, { target: { value: 'algebra' } });
    await waitFor(() => {
      expect(screen.getByTestId('location').textContent).toContain('q=algebra');
    });
  });

  it('clears all filters via Clear filters', async () => {
    renderBank('/teacher/questions?q=hi&subject=1');
    const clear = await screen.findByRole('button', { name: /clear filters/i });
    fireEvent.click(clear);
    await waitFor(() => {
      const loc = screen.getByTestId('location').textContent ?? '';
      expect(loc).toBe('/teacher/questions');
    });
  });

  it('navigates "Use in new set" with the question + returnTo encoded', async () => {
    renderBank('/teacher/questions?q=alg&subject=1');
    const useBtn = await screen.findByRole('button', { name: /use in new set/i });
    fireEvent.click(useBtn);
    await waitFor(() => {
      const loc = screen.getByTestId('location').textContent ?? '';
      expect(loc).toContain('/teacher/problem-sets/new');
      expect(loc).toContain('seedQuestion=100');
      expect(loc).toContain('returnTo=');
      // returnTo should preserve the current filters
      expect(decodeURIComponent(loc)).toContain('q=alg');
    });
  });

  it('navigates Edit with returnTo so the editor can come back', async () => {
    renderBank('/teacher/questions?q=alg');
    // Both the row hover-action and the preview footer have an "Edit" button.
    // Click the row's so we don't depend on the focus-driven footer rendering.
    const editBtns = await screen.findAllByRole('button', { name: /^edit$/i });
    fireEvent.click(editBtns[0]);
    await waitFor(() => {
      const loc = screen.getByTestId('location').textContent ?? '';
      expect(loc).toContain('/teacher/questions/100/edit');
      expect(loc).toContain('returnTo=');
      expect(decodeURIComponent(loc)).toContain('q=alg');
    });
  });
});
