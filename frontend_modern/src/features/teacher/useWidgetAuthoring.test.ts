import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import { useWidgetAuthoring } from './useWidgetAuthoring';
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

describe('useWidgetAuthoring', () => {
  it('POSTs the description to /ai/widget-authoring/ and returns a real proposal', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        widget_kind: 'number-line',
        widget_config: { min: 0, max: 1, step: 0.25, initial: 0.75, label: 'Mark 3/4' },
        model_used: 'claude-sonnet-4-6',
        ai_available: true,
        repaired: false,
      },
    });

    const { result } = renderHook(() => useWidgetAuthoring(), { wrapper });
    result.current.mutate({ description: 'a number line where students mark 3/4' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith('/ai/widget-authoring/', {
      description: 'a number line where students mark 3/4',
    });
    expect(result.current.data?.widget_kind).toBe('number-line');
    expect(result.current.data?.ai_available).toBe(true);
  });

  it('passes through the deterministic stub fallback shape unchanged', async () => {
    // No key / timeout → backend returns the kind's safe default as a stub.
    mockPost.mockResolvedValueOnce({
      data: {
        widget_kind: 'number-line',
        widget_config: { min: 0, max: 10, step: 1, initial: 5, label: 'Number line' },
        model_used: 'stub',
        ai_available: false,
        repaired: false,
      },
    });

    const { result } = renderHook(() => useWidgetAuthoring(), { wrapper });
    result.current.mutate({ description: 'a number line' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.model_used).toBe('stub');
    expect(result.current.data?.ai_available).toBe(false);
    // The config is still present and usable even on the fallback path.
    expect(result.current.data?.widget_config).toMatchObject({ initial: 5 });
  });

  it('forwards a kind_hint when provided', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        widget_kind: 'fraction-bar',
        widget_config: {},
        model_used: 'stub',
        ai_available: false,
        repaired: false,
      },
    });

    const { result } = renderHook(() => useWidgetAuthoring(), { wrapper });
    result.current.mutate({ description: 'show three quarters', kind_hint: 'fraction-bar' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockPost).toHaveBeenCalledWith('/ai/widget-authoring/', {
      description: 'show three quarters',
      kind_hint: 'fraction-bar',
    });
  });

  it('surfaces a transport error so the UI can show the fallback line', async () => {
    mockPost.mockRejectedValueOnce(new Error('503'));

    const { result } = renderHook(() => useWidgetAuthoring(), { wrapper });
    result.current.mutate({ description: 'a number line' });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
