import { useOnlineStatus } from '@/shared/hooks/useOnlineStatus';
import { useT } from '@/shared/i18n/useT';

/**
 * Slim, informational banner shown only while the browser is offline (MSO-2).
 *
 * Warm amber — not a harsh error red: being offline is an honest state, not a
 * failure. `role="status"` + `aria-live="polite"` so screen readers announce
 * the change without interrupting. Renders nothing when online.
 */
export const OfflineBanner = () => {
  const online = useOnlineStatus();
  const t = useT();

  if (online) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-2 bg-amber-100 px-4 py-2 text-center text-sm font-medium text-amber-900"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-4 w-4 shrink-0"
      >
        <path d="m2 2 20 20" />
        <path d="M8.5 16.5a5 5 0 0 1 7 0" />
        <path d="M2 8.82a15 15 0 0 1 4.17-2.65" />
        <path d="M10.66 5c4.01-.36 8.14.9 11.34 3.76" />
        <path d="M16.85 11.25a10 10 0 0 1 2.22 1.68" />
        <path d="M5 13a10 10 0 0 1 5.24-2.76" />
        <line x1="12" y1="20" x2="12.01" y2="20" />
      </svg>
      <span>{t('connectivity.offlineBanner')}</span>
    </div>
  );
};
