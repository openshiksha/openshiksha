import type { LocaleDict } from './en';

/**
 * Marathi (मराठी) locale — LA-9 third-language pilot.
 *
 * A **pilot** locale (registry `coverage: 'pilot'`): a *subset* of the English
 * key set is allowed, and any key not translated here falls back to English at
 * runtime (I18nProvider, principle 3 — English is the fallback, never a blank).
 * The pilot grows surface-by-surface; LA-9b covers the **anonymous journey**
 * (the highest-leverage surface — what a non-English-speaking parent sees before
 * anyone can help them): common / auth hero / login / register.
 *
 * Devanagari script — reuses the existing "Noto Sans Devanagari" font stack
 * (principle 4), so the pilot isolates the framework question (can the switcher
 * / parity / loader handle N>2?) from font work.
 *
 * Register: everyday Maharashtra K-12 Marathi. Classroom-English domain words
 * (युझरनेम, पासवर्ड, ईमेल, CBSE) are kept transliterated as students/parents
 * actually read them. Glossary in docs/initiatives/2026-language-access.md.
 *
 * `satisfies Partial<LocaleDict>` keeps every key checked against the English
 * source of truth (a typo'd key is a compile error) while permitting a subset.
 */
export const mr = {
  // ── Common / switcher ────────────────────────────────────────────────
  'common.language': 'भाषा',
  'common.languageSwitchTo': 'भाषा बदला: {language}',
  'common.cancel': 'रद्द करा',
  'common.practice': 'सराव',
  'common.topicsOne': '{count} विषय',
  'common.topicsMany': '{count} विषय',

  // ── Auth hero (chalkboard panel, shared by login + register) ─────────
  'auth.heroHeadline': 'शिकण्याची गुरुकिल्ली, एकेका प्रश्नातून.',
  'auth.heroSubtext':
    'अनुकूल सराव, तत्काळ तपासणी, आणि प्रत्येक विद्यार्थ्याला पुढे नेमके काय शिकायचे हे दाखवणारे विश्लेषण.',
  'auth.heroFootnote': 'CBSE · इयत्ता 7–10 · English & मराठी',

  // ── Login page ───────────────────────────────────────────────────────
  'login.title': 'पुन्हा स्वागत आहे',
  'login.subtitle': 'शिकणे सुरू ठेवण्यासाठी साइन इन करा.',
  'login.username': 'युझरनेम',
  'login.usernamePlaceholder': 'तुमचे युझरनेम लिहा',
  'login.password': 'पासवर्ड',
  'login.passwordPlaceholder': 'तुमचा पासवर्ड लिहा',
  'login.submit': 'साइन इन करा',
  'login.submitting': 'साइन इन होत आहे…',
  'login.error': 'युझरनेम किंवा पासवर्ड चुकीचा आहे. कृपया पुन्हा प्रयत्न करा.',
  'login.noAccount': 'खाते नाही?',
  'login.registerLink': 'नोंदणी करा',
  'login.schoolQuestion': 'तुम्ही शाळा आहात का?',
  'login.enquireLink': 'OpenShiksha बद्दल विचारा',

  // ── Register page ────────────────────────────────────────────────────
  'register.title': 'तुमचे खाते तयार करा',
  'register.subtitle': 'तुम्हाला कसे शिकायचे आहे?',
  'register.haveAccount': 'आधीच खाते आहे?',
  'register.signIn': 'साइन इन करा',
  'register.back': '← मागे',
  'register.joinSchoolTitle': 'शाळेत सामील व्हा',
  'register.joinSchoolDesc':
    'आपोआप नोंदणीसाठी तुमच्या शिक्षकांकडून मिळालेला क्लासरूम जॉइन कोड वापरा.',
  'register.openTitle': 'स्वतंत्रपणे अभ्यास करा',
  'register.openDesc':
    'सामायिक प्रश्नपेढीतून तुमच्या गतीने सराव करा — शाळेची गरज नाही.',
  'register.openSubtitle': 'सामायिक प्रश्नपेढी मोफत वापरा.',
  'register.schoolTitle': 'तुमच्या शाळेत सामील व्हा',
  'register.schoolSubtitle': 'तुमच्या शिक्षकांकडून मिळालेला जॉइन कोड टाका.',
  'register.firstName': 'नाव',
  'register.lastName': 'आडनाव',
  'register.username': 'युझरनेम',
  'register.password': 'पासवर्ड',
  'register.emailOptional': 'ईमेल (ऐच्छिक)',
  'register.joinCode': 'क्लासरूम जॉइन कोड',
  'register.joinCodePlaceholder': 'उदा. ABC123',
  'register.error': 'नोंदणी होऊ शकली नाही. कृपया पुन्हा प्रयत्न करा.',
  'register.creating': 'खाते तयार होत आहे…',
  'register.startPractising': 'सराव सुरू करा',
  'register.createAccount': 'खाते तयार करा',
} satisfies Partial<LocaleDict>;
