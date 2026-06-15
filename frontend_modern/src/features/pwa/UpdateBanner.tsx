import { useT } from '@/shared/i18n/useT';

interface UpdateBannerProps {
  /** Apply the waiting service worker and reload to the new version. */
  onRefresh: () => void;
}

/**
 * Slim "new version available" banner (MSO-3). Presentational only — the
 * service-worker wiring lives in `PwaUpdater`, so this is unit-testable without
 * the `virtual:pwa-register` module. Mirrors the OfflineBanner slim-banner
 * pattern (no toast system exists), but in brand orange to read as an action
 * rather than a warning.
 */
export const UpdateBanner = ({ onRefresh }: UpdateBannerProps) => {
  const t = useT();
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 top-0 z-50 flex items-center justify-center gap-3 bg-brand-600 px-4 py-2 text-center text-sm font-medium text-white shadow-lift"
    >
      <span>{t('pwa.updateAvailable')}</span>
      <button
        type="button"
        onClick={onRefresh}
        className="rounded-md bg-white/20 px-3 py-1 text-sm font-semibold text-white transition hover:bg-white/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
      >
        {t('pwa.refresh')}
      </button>
    </div>
  );
};
