import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/api/client';

/**
 * MPN-4 — Web Push opt-in.
 *
 * Bridges the browser Push API to the backend (MPN-2):
 *   subscribe()   → Notification.requestPermission → pushManager.subscribe
 *                   (with the server VAPID public key) → POST /push/subscribe/
 *   unsubscribe() → pushManager.unsubscribe → POST /push/unsubscribe/
 *
 * Honest UX (initiative principle 4): if the browser lacks push support, or the
 * server has no VAPID key configured (empty publicKey), `supported` stays false
 * and the UI hides the affordance rather than promising something that can't
 * work. iOS Safari only supports push for *installed* PWAs (16.4+); there the
 * APIs are present only once installed, so this degrades the same way.
 */

const SUBSCRIBE_URL = '/push/subscribe/';
const UNSUBSCRIBE_URL = '/push/unsubscribe/';
const VAPID_KEY_URL = '/push/vapid-public-key/';

/** Decode a base64url VAPID public key into the Uint8Array `subscribe` wants. */
export function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  // Allocate over a concrete ArrayBuffer so the type is Uint8Array<ArrayBuffer>,
  // which is what PushManager.subscribe's applicationServerKey requires.
  const output = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i += 1) output[i] = raw.charCodeAt(i);
  return output;
}

function browserSupportsPush(): boolean {
  return (
    typeof navigator !== 'undefined' &&
    'serviceWorker' in navigator &&
    typeof window !== 'undefined' &&
    'PushManager' in window &&
    'Notification' in window
  );
}

export interface PushSubscriptionState {
  /** Push is usable here: browser support AND a server VAPID key. */
  supported: boolean;
  /** Current Notification permission ('default' | 'granted' | 'denied'). */
  permission: NotificationPermission;
  /** True when this browser currently holds a push subscription. */
  isSubscribed: boolean;
  /** True while subscribe()/unsubscribe() is in flight. */
  busy: boolean;
  subscribe: () => Promise<void>;
  unsubscribe: () => Promise<void>;
}

export function usePushSubscription(): PushSubscriptionState {
  const browserSupported = browserSupportsPush();
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>(
    browserSupported ? Notification.permission : 'default',
  );

  // Fetch the server VAPID public key once; an empty key disables push.
  useEffect(() => {
    if (!browserSupported) return;
    let cancelled = false;
    apiClient
      .get<{ publicKey: string }>(VAPID_KEY_URL)
      .then((res) => {
        if (!cancelled) setPublicKey(res.data.publicKey ?? '');
      })
      .catch(() => {
        if (!cancelled) setPublicKey('');
      });
    return () => {
      cancelled = true;
    };
  }, [browserSupported]);

  // Reflect any existing browser subscription into state.
  useEffect(() => {
    if (!browserSupported) return;
    let cancelled = false;
    navigator.serviceWorker.ready
      .then((reg) => reg.pushManager.getSubscription())
      .then((sub) => {
        if (!cancelled) setIsSubscribed(!!sub);
      })
      .catch(() => {
        /* no SW (dev) — leave isSubscribed false */
      });
    return () => {
      cancelled = true;
    };
  }, [browserSupported]);

  const subscribe = useCallback(async () => {
    if (!browserSupported || !publicKey) return;
    setBusy(true);
    try {
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== 'granted') return;

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
      // toJSON() yields { endpoint, keys: { p256dh, auth } } — exactly the
      // shape POST /push/subscribe/ expects.
      await apiClient.post(SUBSCRIBE_URL, sub.toJSON());
      setIsSubscribed(true);
    } finally {
      setBusy(false);
    }
  }, [browserSupported, publicKey]);

  const unsubscribe = useCallback(async () => {
    if (!browserSupported) return;
    setBusy(true);
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await apiClient
          .post(UNSUBSCRIBE_URL, { endpoint: sub.endpoint })
          .catch(() => {
            /* best-effort server prune; still unsubscribe locally */
          });
        await sub.unsubscribe();
      }
      setIsSubscribed(false);
    } finally {
      setBusy(false);
    }
  }, [browserSupported]);

  return {
    // publicKey === null means "still loading"; treat only a non-empty key as supported.
    supported: browserSupported && !!publicKey,
    permission,
    isSubscribed,
    busy,
    subscribe,
    unsubscribe,
  };
}
