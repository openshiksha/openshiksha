import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ClassroomCodeWidget } from './ClassroomCodeWidget';
import type { ClassroomInviteCode } from '@/types/index';

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}));

vi.mock('@/api/client', () => ({
  apiClient: { get: mockGet, post: mockPost },
}));

function makeCode(overrides: Partial<ClassroomInviteCode> = {}): ClassroomInviteCode {
  return {
    id: 1,
    code: 'ABC123',
    classroom_id: 5,
    classroom_name: 'Std 8 A',
    is_active: true,
    expires_at: null,
    created_at: '2026-06-01T00:00:00Z',
    ...overrides,
  };
}

function renderWidget() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ClassroomCodeWidget classroomId={5} classroomName="Std 8 A" />
    </QueryClientProvider>
  );
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
    configurable: true,
  });
  // jsdom defaults to http://localhost/
});

describe('ClassroomCodeWidget', () => {
  it('renders "No expiry" when expires_at is null', async () => {
    mockGet.mockResolvedValue({ data: [makeCode({ expires_at: null })] });
    renderWidget();
    expect(await screen.findByTestId('join-code-expiry')).toHaveTextContent('No expiry');
  });

  it('renders relative expiry for a dated code', async () => {
    const future = new Date(Date.now() + 6 * 24 * 60 * 60 * 1000).toISOString();
    mockGet.mockResolvedValue({ data: [makeCode({ expires_at: future })] });
    renderWidget();
    const expiry = await screen.findByTestId('join-code-expiry');
    expect(expiry.textContent).toMatch(/Expires in \d+ days/);
  });

  it('marks expiry urgent when less than 48 hours away', async () => {
    const soon = new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString();
    mockGet.mockResolvedValue({ data: [makeCode({ expires_at: soon })] });
    renderWidget();
    const expiry = await screen.findByTestId('join-code-expiry');
    expect(expiry.textContent).toMatch(/Expires in \d+ hour/);
    expect(expiry.className).toMatch(/rose/);
  });

  it('builds a shareable link with the code in the query string', async () => {
    mockGet.mockResolvedValue({ data: [makeCode()] });
    renderWidget();
    const link = await screen.findByTestId('join-code-link');
    expect((link as HTMLInputElement).value).toContain('/register/school?code=ABC123');
  });

  it('copies the shareable link via the Copy link button', async () => {
    mockGet.mockResolvedValue({ data: [makeCode()] });
    renderWidget();
    const copyLinkBtn = await screen.findByRole('button', { name: /copy link/i });
    fireEvent.click(copyLinkBtn);
    await waitFor(() => {
      expect((navigator.clipboard.writeText as ReturnType<typeof vi.fn>)).toHaveBeenCalledWith(
        expect.stringContaining('/register/school?code=ABC123'),
      );
    });
  });

  it('asks for confirmation before regenerating', async () => {
    mockGet.mockResolvedValue({ data: [makeCode()] });
    mockPost.mockResolvedValue({ data: makeCode({ code: 'XYZ789' }) });
    renderWidget();
    const regenBtn = await screen.findByRole('button', { name: /^regenerate$/i });
    fireEvent.click(regenBtn);
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(mockPost).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: /yes, regenerate/i }));
    await waitFor(() => expect(mockPost).toHaveBeenCalledWith(
      '/users/me/classroom-code/',
      { classroom_id: 5 },
    ));
  });

  it('cancels the regenerate confirmation without calling the API', async () => {
    mockGet.mockResolvedValue({ data: [makeCode()] });
    renderWidget();
    fireEvent.click(await screen.findByRole('button', { name: /^regenerate$/i }));
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(mockPost).not.toHaveBeenCalled();
  });
});
