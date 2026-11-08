import { useI18n } from './i18nContext';
import { LOCALES } from './locales/registry';

/**
 * Compact segmented locale toggle ("EN | हिं | …"). One tap switches the whole
 * UI locale (initiative North Star). Renders one button per registered locale
 * (LA-9a), so adding a language to the registry shows it here automatically —
 * no switcher edit. Lives in the navbar (desktop), the mobile account sheet,
 * and the auth pages.
 */
export const LanguageSwitcher = ({ className = '' }: { className?: string }) => {
  const { locale, setLocale, t } = useI18n();

  const segment = (active: boolean) =>
    `min-w-[2.5rem] rounded-md px-2 py-1 text-xs font-semibold transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
      active ? 'bg-brand-100 text-brand-800' : 'text-ink-500 hover:text-ink-900'
    }`;

  return (
    <div
      role="group"
      aria-label={t('common.language')}
      className={`inline-flex items-center gap-0.5 rounded-lg border border-ink-200 bg-white p-0.5 ${className}`}
    >
      {LOCALES.map((meta) => (
        <button
          key={meta.code}
          type="button"
          lang={meta.htmlLang}
          onClick={() => setLocale(meta.code)}
          aria-pressed={locale === meta.code}
          // WCAG 2.5.3 (Label in Name): the accessible name must contain the visible
          // text, so a speech-input user can say "click EN". Lead with the visible
          // label and keep the localized description after it (axe-core 4.14
          // enforces this as `label-content-name-mismatch`).
          aria-label={`${meta.label}, ${t('common.languageSwitchTo', { language: meta.nativeName })}`}
          className={segment(locale === meta.code)}
        >
          {meta.label}
        </button>
      ))}
    </div>
  );
};
