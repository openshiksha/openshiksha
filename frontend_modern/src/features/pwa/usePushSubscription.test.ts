import { renderHook, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { urlBase64ToUint8Array, usePushSubscription } from './usePushSubscription';
import { apiClient } from '@/api/client';

vi.mock('@/api/client', () => ({
  apiClient: { get: vi.fn(), post: vi.fn() },
}));

const mockGet = vi.mocked(apiClient.get);
const mockPost = vi.mocked(apiClient.post);

// A fake PushManager whose subscribe() returns a subscription with a
// browser-shaped toJSON().
function installPushGlobals(opts: { existing?: boolean; permission?: NotificationPermission } = {}) {
  const fakeSub = {
    endpoint: 'https://push.example.com/abc',
    toJSON: () => ({ endpoint: 'https://push.example.com/abc', keys: { p256dh: 'p', auth: 'a' } }),
    unsubscribe: vi.fn(async () => true),
  };
  const pushManager = {
    subscribe: vi.fn(async () => fakeSub),
    getSubscription: vi.fn(async () => (opts.existing ? fakeSub : null)),
  };
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: { ready: Promise.resolve({ pushManager }) },
  });
  // @ts-expect-error test stub
  window.PushManager = function () {};
  // @ts-expect-error test stub
  window.Notification = { permission: opts.permission ?? 'default', requestPermission: vi.fn() };
  return { fakeSub, pushManager };
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
  // @ts-expect-error cleanup
  delete window.PushManager;
  // @ts-expect-error cleanup
  delete window.Notification;
});

describe('urlBase64ToUint8Array', () => {
  it('decodes a base64url key into bytes', () => {
    const out = urlBase64ToUint8Array(btoa('hello').replace(/\+/g, '-').replace(/\//g, '_'));
    expect(out).toBeInstanceOf(Uint8Array);
    expect(String.fromCharCode(...out)).toBe('hello');
  });
});

describe('usePushSubscription', () => {
  it('is unsupported when the server VAPID key is blank', async () => {
    installPushGlobals();
    mockGet.mockResolvedValue({ data: { publicKey: '' } } as never);
    const { result } = renderHook(() => usePushSubscription());
    await waitFor(() => expect(mockGet).toHaveBeenCalled());
    expect(result.current.supported).toBe(false);
  });

  it('is supported when a VAPID key is present', async () => {
    installPushGlobals();
    mockGet.mockResolvedValue({ data: { publicKey: 'BPK' } } as never);
    const { result } = renderHook(() => usePushSubscription());
    await waitFor(() => expect(result.current.supported).toBe(true));
  });

  it('subscribe() posts the serialized subscription payload', async () => {
    const { pushManager } = installPushGlobals({ permission: 'granted' });
    // @ts-expect-error stub returns granted
    window.Notification.requestPermission = vi.fn(async () => 'granted');
    mockGet.mockResolvedValue({ data: { publicKey: btoa('key').replace(/=+$/, '') } } as never);
    mockPost.mockResolvedValue({ data: {} } as never);

    const { result } = renderHook(() => usePushSubscription());
    await waitFor(() => expect(result.current.supported).toBe(true));

    await act(async () => {
      await result.current.subscribe();
    });

    expect(pushManager.subscribe).toHaveBeenCalledWith(
      expect.objectContaining({ userVisibleOnly: true }),
    );
    expect(mockPost).toHaveBeenCalledWith(
      '/push/subscribe/',
      expect.objectContaining({
        endpoint: 'https://push.example.com/abc',
        keys: { p256dh: 'p', auth: 'a' },
      }),
    );
    expect(result.current.isSubscribed).toBe(true);
  });

  it('subscribe() aborts when permission is not granted', async () => {
    installPushGlobals();
    // @ts-expect-error stub returns denied
    window.Notification.requestPermission = vi.fn(async () => 'denied');
    mockGet.mockResolvedValue({ data: { publicKey: 'BPK' } } as never);

    const { result } = renderHook(() => usePushSubscription());
    await waitFor(() => expect(result.current.supported).toBe(true));

    await act(async () => {
      await result.current.subscribe();
    });

    expect(mockPost).not.toHaveBeenCalled();
    expect(result.current.isSubscribed).toBe(false);
  });

  it('reflects an existing subscription and unsubscribe() clears it', async () => {
    const { fakeSub } = installPushGlobals({ existing: true });
    mockGet.mockResolvedValue({ data: { publicKey: 'BPK' } } as never);
    mockPost.mockResolvedValue({ data: {} } as never);

    const { result } = renderHook(() => usePushSubscription());
    await waitFor(() => expect(result.current.isSubscribed).toBe(true));

    await act(async () => {
      await result.current.unsubscribe();
    });

    expect(mockPost).toHaveBeenCalledWith('/push/unsubscribe/', {
      endpoint: 'https://push.example.com/abc',
    });
    expect(fakeSub.unsubscribe).toHaveBeenCalled();
    expect(result.current.isSubscribed).toBe(false);
  });
});
