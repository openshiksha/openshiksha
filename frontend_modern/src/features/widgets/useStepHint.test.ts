import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import { useStepHint } from './useStepHint';
import { apiClient } from '@/api/client';

vi.mock('@/api/client', () => ({
  apiClient: { post: vi.fn() },
}));

const mockPost = vi.mocked(apiClient.post);

const wrapper = ({ children }: { children: ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return createElement(QueryClientProvider, { client: qc }, children);
};

beforeEach(() => {
  mockPost.mockReset();
});

describe('useStepHint', () => {
  it('POSTs the two lines to /ai/step-hint/ and returns a real AI explanation', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        verdict: 'wrong',
        reason: 'These equations have different solutions.',
        hint: 'You took 3 off the left but not the right — subtract it from both sides.',
        model_used: 'claude-sonnet-4-6',
        ai_available: true,
      },
    });

    const { result } = renderHook(() => useStepHint(), { wrapper });
    result.current.mutate({ previous: '2x + 3 = 7', current: '2x = 10' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith('/ai/step-hint/', {
      previous: '2x + 3 = 7',
      current: '2x = 10',
    });
    expect(result.current.data?.verdict).toBe('wrong');
    expect(result.current.data?.ai_available).toBe(true);
    expect(result.current.data?.hint).toContain('subtract');
  });

  it('passes through the deterministic static-hint fallback shape unchanged', async () => {
    // No key / timeout / empty output → backend returns the static hint as a stub.
    mockPost.mockResolvedValueOnce({
      data: {
        verdict: 'wrong',
        reason: 'These equations have different solutions.',
        hint: 'Re-check this line term by term, and watch the signs.',
        model_used: 'stub',
        ai_available: false,
      },
    });

    const { result } = renderHook(() => useStepHint(), { wrapper });
    result.current.mutate({ previous: '2x + 3 = 7', current: '2x = 10' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.verdict).toBe('wrong');
    expect(result.current.data?.ai_available).toBe(false);
    expect(result.current.data?.model_used).toBe('stub');
  });

  it('passes through a correct verdict with no AI call (hint null)', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        verdict: 'correct',
        reason: 'Same solution as the line above.',
        hint: null,
        model_used: null,
        ai_available: false,
      },
    });

    const { result } = renderHook(() => useStepHint(), { wrapper });
    result.current.mutate({ previous: '2x + 3 = 7', current: '2x = 4' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.verdict).toBe('correct');
    expect(result.current.data?.hint).toBeNull();
  });

  it('surfaces a transport error', async () => {
    mockPost.mockRejectedValueOnce(new Error('network down'));

    const { result } = renderHook(() => useStepHint(), { wrapper });
    result.current.mutate({ previous: '2x + 3 = 7', current: '2x = 10' });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('network down');
  });
});
