import { useState } from 'react';
import { usePushSubscription } from './usePushSubscription';
import { useT } from '@/shared/i18n/useT';

/** localStorage key recording that the user dismissed the push affordance. */
export const PUSH_DISMISSED_KEY = 'os-push-dismissed';

const isDismissed = (): boolean => {
  try {
    return localStorage.getItem(PUSH_DISMISSED_KEY) === '1';
  } catch {
    return false;
  }
};

/**
 * MPN-4 — dismissible "Get reminders on your phone" affordance, mirroring the
 * MSO-5 InstallBanner. Shown only when push is usable (browser support + server
 * VAPID key), not already granted/subscribed, not blocked, and not dismissed.
 */
export const PushBanner = () => {
  const { supported, permission, isSubscribed, busy, subscribe } = usePushSubscription();
  const t = useT();
  const [dismissed, setDismissed] = useState(isDismissed);

  if (!supported || isSubscribed || permission === 'denied' || dismissed) return null;

  const dismiss = () => {
    try {
      localStorage.setItem(PUSH_DISMISSED_KEY, '1');
    } catch {
      /* private mode — the prompt simply reappears later */
    }
    setDismissed(true);
  };

  return (
    <div className="flex items-center justify-center gap-3 bg-ink-50 px-4 py-2 text-center text-sm text-ink-700">
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-4 w-4 shrink-0 text-brand-600"
      >
        <path d="M10.268 21a2 2 0 0 0 3.464 0" />
        <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />
      </svg>
      <span className="font-medium">{t('push.prompt')}</span>
      <button
        type="button"
        onClick={subscribe}
        disabled={busy}
        className="rounded-md bg-brand-600 px-3 py-1 text-sm font-semibold text-white transition hover:bg-brand-700 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-300 disabled:opacity-60"
      >
        {t('push.enable')}
      </button>
      <button
        type="button"
        onClick={dismiss}
        aria-label={t('push.dismiss')}
        className="rounded-md px-2 py-1 text-ink-500 transition hover:text-ink-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-300"
      >
        ✕
      </button>
    </div>
  );
};
