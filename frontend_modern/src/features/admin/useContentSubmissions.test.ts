import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import {
  useContentSubmission,
  useContentSubmissions,
  useSubmissionTransition,
} from './useContentSubmissions';
import { apiClient } from '@/api/client';

vi.mock('@/api/client', () => ({
  apiClient: { get: vi.fn(), post: vi.fn() },
}));

const mockGet = vi.mocked(apiClient.get);
const mockPost = vi.mocked(apiClient.post);

const wrapper = ({ children }: { children: ReactNode }) => {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return createElement(QueryClientProvider, { client: qc }, children);
};

const summaryRow = {
  id: 7,
  name: 'Fractions pack',
  pack_hash: 'abc123',
  provenance: { author: 'Asha', license: 'CC-BY-4.0' },
  state: 'pending',
  state_display: 'Pending review',
  note: '',
  reviewer_username: null,
  question_count: 2,
  created_at: '2026-07-07T00:00:00Z',
  updated_at: '2026-07-07T00:00:00Z',
  reviewed_at: null,
};

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('useContentSubmissions', () => {
  it('fetches the queue filtered by state and unwraps the paginated results', async () => {
    mockGet.mockResolvedValueOnce({ data: { count: 1, results: [summaryRow] } });

    const { result } = renderHook(() => useContentSubmissions('pending'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith('/content-submissions/', {
      params: { state: 'pending' },
    });
    expect(result.current.data).toEqual([summaryRow]);
  });

  it('omits the state param when filtering to all', async () => {
    mockGet.mockResolvedValueOnce({ data: { count: 0, results: [] } });

    const { result } = renderHook(() => useContentSubmissions('all'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith('/content-submissions/', { params: {} });
  });
});

describe('useContentSubmission', () => {
  it('fetches the detail (payload included) for the given id', async () => {
    const detail = { ...summaryRow, payload: { pack_version: '1.0', questions: [] } };
    mockGet.mockResolvedValueOnce({ data: detail });

    const { result } = renderHook(() => useContentSubmission(7), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockGet).toHaveBeenCalledWith('/content-submissions/7/');
    expect(result.current.data?.payload?.pack_version).toBe('1.0');
  });

  it('does not fetch until an id is selected', () => {
    renderHook(() => useContentSubmission(null), { wrapper });
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('useSubmissionTransition', () => {
  it('POSTs approve without a body when no note is given', async () => {
    mockPost.mockResolvedValueOnce({ data: { ...summaryRow, state: 'approved' } });

    const { result } = renderHook(() => useSubmissionTransition(), { wrapper });
    result.current.mutate({ id: 7, action: 'approve' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith('/content-submissions/7/approve/', {});
  });

  it('POSTs reject with the note in the body', async () => {
    mockPost.mockResolvedValueOnce({ data: { ...summaryRow, state: 'rejected' } });

    const { result } = renderHook(() => useSubmissionTransition(), { wrapper });
    result.current.mutate({ id: 7, action: 'reject', note: 'Answers to Q2 are wrong.' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith('/content-submissions/7/reject/', {
      note: 'Answers to Q2 are wrong.',
    });
  });

  it('surfaces a server 409 (illegal transition) as an error', async () => {
    mockPost.mockRejectedValueOnce({
      response: { status: 409, data: { detail: 'Cannot approve from rejected.' } },
    });

    const { result } = renderHook(() => useSubmissionTransition(), { wrapper });
    result.current.mutate({ id: 7, action: 'approve' });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
