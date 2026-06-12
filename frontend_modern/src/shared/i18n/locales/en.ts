/**
 * English locale — the source of truth for i18n keys.
 *
 * Every UI string lives here as a flat key → string map. `LocaleKey` is
 * derived from this object, so a typo'd key in a `t()` call is a type error,
 * and the Hindi dictionary is type-checked against the same key set
 * (see locales/hi.ts). Keys are namespaced `surface.element`.
 *
 * Interpolation uses `{var}` placeholders: t('common.greeting', { name }).
 */
export const en = {
  // ── Common / switcher ────────────────────────────────────────────────
  'common.language': 'Language',
  'common.languageSwitchTo': 'Switch language to {language}',

  // ── Auth hero (chalkboard panel, shared by login + register) ─────────
  'auth.heroHeadline': 'Unlock learning, one question at a time.',
  'auth.heroSubtext':
    'Adaptive practice, instant correction, and analytics that show every student exactly what to learn next.',
  'auth.heroFootnote': 'CBSE · Classes 7–10 · English & हिन्दी',

  // ── Login page ───────────────────────────────────────────────────────
  'login.title': 'Welcome back',
  'login.subtitle': 'Sign in to continue learning.',
  'login.username': 'Username',
  'login.usernamePlaceholder': 'Enter your username',
  'login.password': 'Password',
  'login.passwordPlaceholder': 'Enter your password',
  'login.submit': 'Sign in',
  'login.submitting': 'Signing in…',
  'login.error': 'Invalid username or password. Please try again.',
  'login.noAccount': "Don't have an account?",
  'login.registerLink': 'Register',
  'login.schoolQuestion': 'Are you a school?',
  'login.enquireLink': 'Enquire about OpenShiksha',
} as const;

/** Every valid i18n key. Derived from the English dictionary. */
export type LocaleKey = keyof typeof en;

/** Shape every non-English locale must satisfy — full key parity, enforced by tsc. */
export type LocaleDict = Record<LocaleKey, string>;
