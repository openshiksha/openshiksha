import { useInstallPrompt } from './useInstallPrompt';
import { useT } from '@/shared/i18n/useT';

/**
 * Dismissible "Add to home screen" affordance (MSO-5). A slim, unobtrusive
 * banner — not a modal — shown only when the browser has offered an install
 * prompt and the user hasn't already dismissed it or installed the app. iOS
 * Safari never fires `beforeinstallprompt`, so this stays hidden there.
 */
export const InstallBanner = () => {
  const { canInstall, promptInstall, dismiss } = useInstallPrompt();
  const t = useT();

  if (!canInstall) return null;

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
        <path d="M12 17V3" />
        <path d="m6 11 6 6 6-6" />
        <path d="M19 21H5" />
      </svg>
      <span className="font-medium">{t('pwa.installPrompt')}</span>
      <button
        type="button"
        onClick={promptInstall}
        className="rounded-md bg-brand-600 px-3 py-1 text-sm font-semibold text-white transition hover:bg-brand-700 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-300"
      >
        {t('pwa.install')}
      </button>
      <button
        type="button"
        onClick={dismiss}
        aria-label={t('pwa.installDismiss')}
        className="rounded-md px-2 py-1 text-ink-500 transition hover:text-ink-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-300"
      >
        ✕
      </button>
    </div>
  );
};
