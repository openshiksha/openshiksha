import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import { usePracticeProblem } from './usePracticeProblem';
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

describe('usePracticeProblem', () => {
  it('POSTs the topic to /ai/practice-problem/ and returns a verified real proposal', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        widget_kind: 'number-line',
        widget_config: { min: 0, max: 1, step: 0.5 },
        correct_answer: { answer: 0.5 },
        model_used: 'claude-sonnet-4-6',
        ai_available: true,
        repaired: false,
        verdict_code: 'ok',
      },
    });

    const { result } = renderHook(() => usePracticeProblem(), { wrapper });
    result.current.mutate({ topic: 'mark 1/2 on a number line' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith('/ai/practice-problem/', {
      topic: 'mark 1/2 on a number line',
    });
    expect(result.current.data?.widget_kind).toBe('number-line');
    expect(result.current.data?.correct_answer.answer).toBe(0.5);
    expect(result.current.data?.ai_available).toBe(true);
    expect(result.current.data?.verdict_code).toBe('ok');
  });

  it('passes through a snap-repaired proposal shape unchanged (¾ → 0.8)', async () => {
    // The AI proposed 0.75 on a step-0.25 grid; the backend deterministically
    // snapped it to the reachable 0.8 and flagged `repaired`.
    mockPost.mockResolvedValueOnce({
      data: {
        widget_kind: 'number-line',
        widget_config: { min: 0, max: 1, step: 0.25 },
        correct_answer: { answer: 0.8 },
        model_used: 'claude-sonnet-4-6',
        ai_available: true,
        repaired: true,
        verdict_code: 'ok',
      },
    });

    const { result } = renderHook(() => usePracticeProblem(), { wrapper });
    result.current.mutate({ topic: 'mark 3/4 on a number line' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.correct_answer.answer).toBe(0.8);
    expect(result.current.data?.repaired).toBe(true);
    expect(result.current.data?.ai_available).toBe(true);
  });

  it('passes through the deterministic safe-default fallback shape unchanged', async () => {
    // No key / unsalvageable proposal → backend returns the known-good, PV-1-
    // passed safe problem as a non-AI default.
    mockPost.mockResolvedValueOnce({
      data: {
        widget_kind: 'number-line',
        widget_config: { min: 0, max: 1, step: 0.5 },
        correct_answer: { answer: 0.5 },
        model_used: 'stub',
        ai_available: false,
        repaired: false,
        verdict_code: 'safe_default',
      },
    });

    const { result } = renderHook(() => usePracticeProblem(), { wrapper });
    result.current.mutate({ topic: 'something the AI cannot do' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.ai_available).toBe(false);
    expect(result.current.data?.model_used).toBe('stub');
    expect(result.current.data?.verdict_code).toBe('safe_default');
  });

  it('surfaces a transport error', async () => {
    mockPost.mockRejectedValueOnce(new Error('network down'));

    const { result } = renderHook(() => usePracticeProblem(), { wrapper });
    result.current.mutate({ topic: 'mark 1/2 on a number line' });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('network down');
  });
});
