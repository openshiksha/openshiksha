import type { LocaleDict } from './en';

/**
 * Hindi (हिंदी) locale. Loaded lazily — see I18nProvider — so the entry chunk
 * stays inside the performance budget.
 *
 * Register: everyday K-12 Hindi per the initiative Glossary
 * (docs/initiatives/2026-language-access.md). Classroom-English domain words
 * (Assignment, Dashboard, Score…) are transliterated, not academically
 * translated. `LocaleDict` enforces key parity with English at compile time;
 * the runtime parity test (LA-5) guards it in CI too.
 */
export const hi: LocaleDict = {
  // ── Common / switcher ────────────────────────────────────────────────
  'common.language': 'भाषा',
  'common.languageSwitchTo': 'भाषा बदलें: {language}',

  // ── Auth hero (chalkboard panel, shared by login + register) ─────────
  'auth.heroHeadline': 'सीखने की कुंजी, एक-एक सवाल से।',
  'auth.heroSubtext':
    'आपकी गति से अभ्यास, तुरंत जाँच, और ऐसी जानकारी जो हर विद्यार्थी को बताए कि आगे क्या सीखना है।',
  'auth.heroFootnote': 'CBSE · कक्षा 7–10 · English & हिन्दी',

  // ── Login page ───────────────────────────────────────────────────────
  'login.title': 'वापसी पर स्वागत है',
  'login.subtitle': 'सीखना जारी रखने के लिए साइन इन करें।',
  'login.username': 'यूज़रनेम',
  'login.usernamePlaceholder': 'अपना यूज़रनेम लिखें',
  'login.password': 'पासवर्ड',
  'login.passwordPlaceholder': 'अपना पासवर्ड लिखें',
  'login.submit': 'साइन इन करें',
  'login.submitting': 'साइन इन हो रहा है…',
  'login.error': 'यूज़रनेम या पासवर्ड गलत है। कृपया फिर से कोशिश करें।',
  'login.noAccount': 'खाता नहीं है?',
  'login.registerLink': 'रजिस्टर करें',
  'login.schoolQuestion': 'क्या आप एक स्कूल हैं?',
  'login.enquireLink': 'OpenShiksha के बारे में पूछें',
};
