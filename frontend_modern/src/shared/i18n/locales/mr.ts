import type { LocaleDict } from './en';

/**
 * Marathi (मराठी) locale — a **pilot** dictionary (subset coverage).
 *
 * Per the registry North Star, a regional language ships surface-by-surface:
 * this pilot covers the student loop the launch video films — the switcher,
 * auth/login, the student dashboard + assignment list, streaks, and the
 * offline/sync surfaces (shots 7 & 8). Every key it *does* define is guarded by
 * the parity test (must exist in English, matching `{var}` placeholders, never
 * blank); everything not listed here falls back to English at runtime
 * (principle 3 — English is the fallback, never a blank).
 *
 * Typed `Partial<LocaleDict>` because a pilot is intentionally a subset. As more
 * surfaces graduate, add their keys here and raise the floor in coverage.test.ts.
 * Classroom-English domain words (Dashboard, Assignment, CBSE, OpenShiksha) are
 * transliterated/kept, matching the Hindi convention.
 */
export const mr: Partial<LocaleDict> = {
  // ── Common / switcher ────────────────────────────────────────────────
  'common.language': 'भाषा',
  'common.languageSwitchTo': 'भाषा बदला: {language}',
  'common.cancel': 'रद्द करा',
  'common.practice': 'सराव',
  'common.topicsOne': '{count} विषय',
  'common.topicsMany': '{count} विषय',

  // ── Auth hero (chalkboard panel, shared by login + register) ─────────
  'auth.heroHeadline': 'शिकण्याची किल्ली, एक-एक प्रश्नातून.',
  'auth.heroSubtext':
    'तुमच्या गतीने सराव, त्वरित तपासणी, आणि प्रत्येक विद्यार्थ्याला पुढे काय शिकायचे हे सांगणारी माहिती.',
  'auth.heroFootnote': 'CBSE · इयत्ता 7–10 · English & मराठी',

  // ── Login page ───────────────────────────────────────────────────────
  'login.title': 'पुन्हा स्वागत आहे',
  'login.subtitle': 'शिकणे सुरू ठेवण्यासाठी साइन इन करा.',
  'login.username': 'वापरकर्तानाव',
  'login.usernamePlaceholder': 'तुमचे वापरकर्तानाव टाका',
  'login.password': 'पासवर्ड',
  'login.passwordPlaceholder': 'तुमचा पासवर्ड टाका',
  'login.submit': 'साइन इन',
  'login.submitting': 'साइन इन करत आहे…',
  'login.error': 'चुकीचे वापरकर्तानाव किंवा पासवर्ड. कृपया पुन्हा प्रयत्न करा.',
  'login.noAccount': 'खाते नाही?',
  'login.registerLink': 'नोंदणी करा',
  'login.schoolQuestion': 'तुम्ही शाळा आहात का?',
  'login.enquireLink': 'OpenShiksha बद्दल चौकशी करा',

  // ── Student dashboard ────────────────────────────────────────────────
  'dashboard.greeting': 'नमस्कार, {name}!',
  'dashboard.title': 'तुमचा डॅशबोर्ड',
  'dashboard.subtitle': 'ही तुमची असाइनमेंट्स आहेत.',
  'dashboard.myProgress': 'माझी प्रगती →',
  'dashboard.loadError': 'असाइनमेंट्स लोड होऊ शकल्या नाहीत. कृपया पान रिफ्रेश करा.',
  'dashboard.openEmptyTitle': 'तुम्ही अजून कोणत्याही वर्गात नोंदणी केलेली नाही',
  'dashboard.openEmptyDescription':
    'स्वतः सराव सुरू करण्यासाठी सामायिक प्रश्नसंच पाहा.',
  'dashboard.browseSubjects': 'विषय पाहा →',

  // ── Assignment list ──────────────────────────────────────────────────
  'assignments.emptyTitle': 'अजून असाइनमेंट नाही',
  'assignments.emptyDescription': 'तुमचे शिक्षक लवकरच काही देतील. नंतर पुन्हा पाहा!',
  'assignments.sectionOverdue': 'मुदत उलटलेली',
  'assignments.sectionDueSoon': 'लवकरच देय',
  'assignments.sectionUpcoming': 'आगामी',
  'assignments.sectionCompleted': 'पूर्ण झालेली',

  // ── Assignment card ──────────────────────────────────────────────────
  'assignment.overdueBy': '{distance} मुदत उलटली',
  'assignment.dueIn': 'देय {distance}',
  'assignment.submittedAgo': '{distance} पूर्वी सादर केले',
  'assignment.submitted': 'सादर केले',
  'assignment.remedialBadge': 'उपचारात्मक सराव',
  'assignment.progress': 'प्रगती',
  'assignment.ctaReview': 'पुनरावलोकन',
  'assignment.ctaContinue': 'सुरू ठेवा',
  'assignment.ctaStart': 'सुरू करा',

  // ── Streak badge ─────────────────────────────────────────────────────
  'streak.days': '{count}-दिवसांची मालिका',
  'streak.tierStarter': 'जोरात',
  'streak.tierWeek': 'आठवड्याचा योद्धा',
  'streak.tierMonth': 'महिन्याचा मास्टर',
  'streak.tierChampion': 'विजेता',
  'streak.best': 'सर्वोत्तम: {count}',
  'streak.grace': 'सूट ✓',
  'streak.graceTitle': 'सवलतीचा दिवस वापरला — एक दिवस चुकूनही मालिका कायम राहिली',

  // ── Connectivity banner ──────────────────────────────────────────────
  'connectivity.offlineTitle': 'तुम्ही ऑफलाइन आहात',
  'connectivity.offlineBanner': 'तुम्ही ऑफलाइन आहात — जतन केलेले काम दाखवत आहे.',
  'connectivity.backOnline': 'पुन्हा ऑनलाइन.',

  // ── Offline sync status ──────────────────────────────────────────────
  'sync.savedOffline': 'या डिव्हाइसवर जतन केले · तुम्ही ऑनलाइन आल्यावर सिंक होईल',
  'sync.syncing': 'सिंक होत आहे…',
  'sync.synced': 'जतन केले',
  'sync.syncFailed': 'सिंक होऊ शकले नाही — पुन्हा प्रयत्न करेल',
  'sync.pendingOne': '{count} बदल सिंक होण्याच्या प्रतीक्षेत',
  'sync.pendingMany': '{count} बदल सिंक होण्याच्या प्रतीक्षेत',

  // ── PWA install + update prompts ─────────────────────────────────────
  'pwa.installPrompt': 'OpenShiksha तुमच्या होम स्क्रीनवर जोडा.',
  'pwa.install': 'इंस्टॉल करा',
  'pwa.installDismiss': 'इंस्टॉल सूचना बंद करा',
  'pwa.updateAvailable': 'नवीन आवृत्ती उपलब्ध आहे.',
  'pwa.refresh': 'रिफ्रेश करा',

  // ── Web Push notifications ───────────────────────────────────────────
  'push.prompt': 'तुमच्या फोनवर रिमाइंडर मिळवा.',
  'push.enable': 'चालू करा',
  'push.dismiss': 'सूचना विनंती बंद करा',
  'push.enabled': 'रिमाइंडर चालू',
  'push.label': 'पुश सूचना',
  'push.description': 'असाइनमेंट लवकरच देय असताना या डिव्हाइसवर सूचना मिळवा.',
  'push.blocked': 'तुमच्या ब्राउझर सेटिंग्जमध्ये सूचना अवरोधित आहेत.',
};
