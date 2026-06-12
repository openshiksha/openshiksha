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
  'common.cancel': 'रद्द करें',
  'common.practice': 'अभ्यास',
  'common.topicsOne': '{count} विषय',
  'common.topicsMany': '{count} विषय',

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

  // ── Student dashboard ────────────────────────────────────────────────
  'dashboard.greeting': 'नमस्ते, {name}!',
  'dashboard.title': 'आपका डैशबोर्ड',
  'dashboard.subtitle': 'ये रहे आपके असाइनमेंट।',
  'dashboard.myProgress': 'मेरी प्रगति →',
  'dashboard.loadError': 'असाइनमेंट लोड नहीं हो पाए। कृपया पेज रीफ़्रेश करें।',
  'dashboard.openEmptyTitle': 'आप अभी किसी क्लासरूम में नहीं हैं',
  'dashboard.openEmptyDescription': 'अपने आप अभ्यास शुरू करने के लिए साझा प्रश्न बैंक देखें।',
  'dashboard.browseSubjects': 'विषय देखें →',

  // ── Assignment list (sections + empty state) ─────────────────────────
  'assignments.emptyTitle': 'अभी कोई असाइनमेंट नहीं',
  'assignments.emptyDescription': 'आपके शिक्षक जल्द ही असाइनमेंट देंगे। बाद में फिर देखें!',
  'assignments.sectionOverdue': 'समय निकल गया',
  'assignments.sectionDueSoon': 'जल्द जमा करें',
  'assignments.sectionUpcoming': 'आने वाले',
  'assignments.sectionCompleted': 'पूरे हो गए',

  // ── Assignment card ──────────────────────────────────────────────────
  'assignment.overdueBy': '{distance} देर हो चुकी',
  'assignment.dueIn': 'अंतिम तिथि: {distance}',
  'assignment.submittedAgo': '{distance} जमा किया',
  'assignment.submitted': 'जमा हो गया',
  'assignment.remedialBadge': 'सुधार अभ्यास',
  'assignment.progress': 'प्रगति',
  'assignment.ctaReview': 'देखें',
  'assignment.ctaContinue': 'जारी रखें',
  'assignment.ctaStart': 'शुरू करें',

  // ── Assignment detail (work + submit flow) ───────────────────────────
  'assignmentDetail.back': 'असाइनमेंट पर वापस जाएँ',
  'assignmentDetail.answeredCount': '{total} में से {answered} उत्तर दिए',
  'assignmentDetail.submittedNice': 'असाइनमेंट जमा हो गया — शाबाश!',
  'assignmentDetail.submittedTitle': 'जमा हो गया',
  'assignmentDetail.grading': 'जाँच चल रही है…',
  'assignmentDetail.notFoundTitle': 'असाइनमेंट नहीं मिला',
  'assignmentDetail.notFoundDescription':
    'यह हटाया जा चुका हो सकता है या आपके पास इसकी अनुमति नहीं है।',
  'assignmentDetail.backToDashboard': 'डैशबोर्ड पर वापस जाएँ',
  'assignmentDetail.noQuestions': 'इस असाइनमेंट में कोई प्रश्न नहीं है',
  'assignmentDetail.submit': 'असाइनमेंट जमा करें',
  'assignmentDetail.confirmTitle': 'असाइनमेंट जमा करें?',
  'assignmentDetail.confirmBody':
    'आपने {total} में से {answered} प्रश्नों के उत्तर दिए हैं। जमा करने के बाद आप उत्तर नहीं बदल पाएँगे।',
  'assignmentDetail.confirmSubmit': 'जमा करें',
  'assignmentDetail.submitting': 'जमा हो रहा है…',

  // ── Due for Review panel (SRS) ───────────────────────────────────────
  'dueReview.title': 'दोहराव के लिए तैयार',
  'dueReview.overdueCount': '{count} का समय निकल गया',
  'dueReview.statusOverdue': 'समय निकल गया',
  'dueReview.statusToday': 'आज करना है',
  'dueReview.statusSoon': 'आगे आने वाला',
  'dueReview.overdueSince': '{date} से बाकी',
  'dueReview.dueOn': 'अंतिम तिथि {date}',
  'dueReview.interval': 'हर {days} दिन',
  'dueReview.reviewedTimes': '{count} बार दोहराया',
  'dueReview.moreTopics': '+{count} और विषय',
  'dueReview.emptyDescription':
    'अभी कुछ बाकी नहीं — कुछ असाइनमेंट पूरे करें, आपका दोहराव कार्यक्रम यहाँ दिखेगा।',
  'dueReview.footer': 'दोहराव की तिथियाँ आगे बढ़ाने के लिए अपने असाइनमेंट का अभ्यास करें।',

  // ── Recommendations panel ────────────────────────────────────────────
  'recommendations.title': 'आगे किसका अभ्यास करें',
  'recommendations.todaysPlan': 'आज की योजना: ~{minutes} मिनट',
  'recommendations.yourScore': 'आपका स्कोर',
  'recommendations.planTopicsOne': 'आज की योजना में {count} विषय',
  'recommendations.planTopicsMany': 'आज की योजना में {count} विषय',
  'recommendations.viewProgress': 'प्रगति देखें →',
  'recommendations.viewLearningPath': 'लर्निंग पाथ देखें →',
  'recommendations.emptyDescription':
    'अभी कोई सुझाव नहीं — कुछ असाइनमेंट प्रश्नों के उत्तर दें, हम आपको दोहराने लायक अध्याय बताएँगे।',

  // ── Explanation panel (AI) ───────────────────────────────────────────
  'explanation.cta': '✨ इस उत्तर को समझाएँ',
  'explanation.whyRight': 'यह उत्तर सही क्यों है',
  'explanation.whereWrong': 'कहाँ गलती हुई',
  'explanation.writing': 'आपकी व्याख्या लिखी जा रही है…',
  'explanation.error': 'अभी व्याख्या नहीं मिल पाई। कृपया थोड़ी देर में फिर कोशिश करें।',
  'explanation.retry': 'फिर कोशिश करें',
  'explanation.stubNote':
    'बिना AI मॉडल के बनाई गई — AI जुड़ने पर व्याख्याएँ और बेहतर होंगी।',
  'explanation.regenerateInLocale': 'हिंदी में समझाएँ',
  'explanation.regenerating': 'फिर से लिखी जा रही है…',

  // ── Streak badge ─────────────────────────────────────────────────────
  'streak.days': '{count} दिन की स्ट्रीक',
  'streak.tierStarter': 'जोश में',
  'streak.tierWeek': 'हफ़्ते के हीरो',
  'streak.tierMonth': 'महीने के मास्टर',
  'streak.tierChampion': 'चैंपियन',
  'streak.best': 'सर्वश्रेष्ठ: {count}',
  'streak.grace': 'ग्रेस ✓',
  'streak.graceTitle': 'ग्रेस दिन इस्तेमाल हुआ — एक दिन छूटने पर भी स्ट्रीक बनी रही',
};
