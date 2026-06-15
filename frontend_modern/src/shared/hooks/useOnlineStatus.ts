import { useEffect, useState } from 'react';

/**
 * Tracks browser connectivity via `navigator.onLine` + the `online`/`offline`
 * window events. Returns `true` when online.
 *
 * Caveat: `navigator.onLine` is optimistic — it reports `true` whenever there's
 * *any* network interface, even behind a captive portal that can't reach our
 * API. So this is fine for an informational banner, but do **not** gate data
 * fetching on it: React Query already handles real fetch failures. (MSO-2)
 *
 * SSR/test-safe: defaults to `true` when `navigator` is undefined.
 */
export const useOnlineStatus = (): boolean => {
  const [online, setOnline] = useState<boolean>(() =>
    typeof navigator === 'undefined' ? true : navigator.onLine,
  );

  useEffect(() => {
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  return online;
};
