import { useI18n, type Translate } from './i18nContext';

/**
 * Shorthand for components that only translate:
 *
 *   const t = useT();
 *   <h1>{t('login.title')}</h1>
 *   <p>{t('common.greeting', { name })}</p>
 */
export const useT = (): Translate => useI18n().t;
