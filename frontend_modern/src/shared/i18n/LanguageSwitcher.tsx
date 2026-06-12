import { useI18n } from './i18nContext';

/**
 * Compact "EN | हिं" segmented toggle. One tap switches the whole UI locale
 * (initiative North Star). Lives in the navbar (desktop), the mobile account
 * sheet, and the auth pages.
 */
export const LanguageSwitcher = ({ className = '' }: { className?: string }) => {
  const { locale, setLocale, t } = useI18n();

  const segment = (active: boolean) =>
    `min-w-[2.5rem] rounded-md px-2 py-1 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
      active ? 'bg-brand-100 text-brand-800' : 'text-ink-500 hover:text-ink-900'
    }`;

  return (
    <div
      role="group"
      aria-label={t('common.language')}
      className={`inline-flex items-center gap-0.5 rounded-lg border border-ink-200 bg-white p-0.5 ${className}`}
    >
      <button
        type="button"
        onClick={() => setLocale('en')}
        aria-pressed={locale === 'en'}
        aria-label={t('common.languageSwitchTo', { language: 'English' })}
        className={segment(locale === 'en')}
      >
        EN
      </button>
      <button
        type="button"
        lang="hi"
        onClick={() => setLocale('hi')}
        aria-pressed={locale === 'hi'}
        aria-label={t('common.languageSwitchTo', { language: 'हिंदी' })}
        className={segment(locale === 'hi')}
      >
        हिं
      </button>
    </div>
  );
};
