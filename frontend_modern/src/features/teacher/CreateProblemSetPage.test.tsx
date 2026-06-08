import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { CreateProblemSetPage } from './CreateProblemSetPage';

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet, post: mockPost },
}));

beforeEach(() => {
  mockGet.mockReset();
  mockGet.mockImplementation((url: string) => {
    if (url.startsWith('/subject-rooms')) return Promise.resolve({ data: { results: [] } });
    if (url.startsWith('/chapters')) return Promise.resolve({ data: [] });
    if (url.startsWith('/questions')) return Promise.resolve({ data: { results: [] } });
    return Promise.resolve({ data: [] });
  });
});

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/teacher/problem-sets/new']}>
        <CreateProblemSetPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('CreateProblemSetPage — mobile sticky action bar (TW-7)', () => {
  it('renders a mobile-only Create bar that is disabled until the form is valid', async () => {
    renderPage();
    const bar = await screen.findByTestId('mobile-create-bar');
    expect(bar.className).toMatch(/lg:hidden/);
    const btn = bar.querySelector('button');
    await waitFor(() => expect(btn).not.toBeNull());
    expect((btn as HTMLButtonElement).disabled).toBe(true);
    // Hint copy should guide the teacher.
    expect(bar.textContent).toMatch(/pick a subject, chapter, title/i);
  });
});
