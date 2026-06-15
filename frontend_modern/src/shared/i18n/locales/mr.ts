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

  // ── Student dashboard (LA-9c) ────────────────────────────────────────
  'dashboard.greeting': 'नमस्कार, {name}!',
  'dashboard.title': 'तुमचा डॅशबोर्ड',
  'dashboard.subtitle': 'ही तुमची असाइनमेंट्स आहेत.',
  'dashboard.myProgress': 'माझी प्रगती →',
  'dashboard.loadError': 'असाइनमेंट्स लोड होऊ शकली नाहीत. कृपया पान रिफ्रेश करा.',
  'dashboard.openEmptyTitle': 'तुम्ही अजून कोणत्याही वर्गात नोंदलेले नाही',
  'dashboard.openEmptyDescription':
    'स्वतः सराव सुरू करण्यासाठी सामायिक प्रश्नपेढी पाहा.',
  'dashboard.browseSubjects': 'विषय पाहा →',

  // ── Assignment list sections + cards ─────────────────────────────────
  'assignments.emptyTitle': 'अजून कोणतीही असाइनमेंट नाही',
  'assignments.emptyDescription': 'तुमचे शिक्षक लवकरच काही देतील. नंतर पुन्हा पाहा!',
  'assignments.sectionOverdue': 'मुदत संपलेली',
  'assignments.sectionDueSoon': 'लवकरच मुदत',
  'assignments.sectionUpcoming': 'येणारी',
  'assignments.sectionCompleted': 'पूर्ण झालेली',
  'assignment.overdueBy': '{distance} ने मुदत संपली',
  'assignment.dueIn': 'मुदत {distance}',
  'assignment.submittedAgo': '{distance} सादर केले',
  'assignment.submitted': 'सादर केले',
  'assignment.remedialBadge': 'पुनरावृत्ती सराव',
  'assignment.progress': 'प्रगती',
  'assignment.ctaReview': 'पुनरावलोकन',
  'assignment.ctaContinue': 'सुरू ठेवा',
  'assignment.ctaStart': 'सुरू करा',

  // ── Assignment detail + submission flow ──────────────────────────────
  'assignmentDetail.back': 'असाइनमेंट्सकडे परत',
  'assignmentDetail.answeredCount': '{total} पैकी {answered} उत्तरे दिली',
  'assignmentDetail.submittedNice': 'असाइनमेंट सादर झाली — छान काम!',
  'assignmentDetail.submittedTitle': 'सादर केले',
  'assignmentDetail.grading': 'तपासणी सुरू आहे…',
  'assignmentDetail.notFoundTitle': 'असाइनमेंट सापडली नाही',
  'assignmentDetail.notFoundDescription': 'ती काढून टाकली असावी किंवा तुम्हाला प्रवेश नाही.',
  'assignmentDetail.backToDashboard': 'डॅशबोर्डकडे परत',
  'assignmentDetail.noQuestions': 'या असाइनमेंटमध्ये कोणतेही प्रश्न नाहीत',
  'assignmentDetail.submit': 'असाइनमेंट सादर करा',
  'assignmentDetail.confirmTitle': 'असाइनमेंट सादर करायची?',
  'assignmentDetail.confirmBody':
    'तुम्ही {total} पैकी {answered} प्रश्नांची उत्तरे दिली आहेत. सादर केल्यानंतर तुम्ही उत्तरे बदलू शकणार नाही.',
  'assignmentDetail.confirmSubmit': 'सादर करा',
  'assignmentDetail.submitting': 'सादर होत आहे…',

  // ── Due-for-review (SRS) ─────────────────────────────────────────────
  'dueReview.title': 'पुनरावलोकनासाठी देय',
  'dueReview.overdueCount': '{count} मुदत संपलेली',
  'dueReview.statusOverdue': 'मुदत संपलेली',
  'dueReview.statusToday': 'आज देय',
  'dueReview.statusSoon': 'लवकरच',
  'dueReview.overdueSince': '{date} पासून मुदत संपली',
  'dueReview.dueOn': 'मुदत {date}',
  'dueReview.interval': 'दर {days} दिवसांनी',
  'dueReview.reviewedTimes': '{count}× पुनरावलोकन केले',
  'dueReview.moreTopics': '+{count} अधिक विषय',
  'dueReview.emptyDescription':
    'अजून काही देय नाही — काही असाइनमेंट्स पूर्ण करा आणि तुमचे पुनरावलोकन वेळापत्रक इथे दिसेल.',
  'dueReview.footer': 'पुनरावलोकनाच्या तारखा पुढे ढकलण्यासाठी तुमच्या असाइनमेंट्सचा सराव करा.',

  // ── Recommendations ("what to practise next") ────────────────────────
  'recommendations.title': 'पुढे काय सराव करायचा',
  'recommendations.todaysPlan': 'आजची योजना: ~{minutes} मिनिटे',
  'recommendations.yourScore': 'तुमचे गुण',
  'recommendations.planTopicsOne': 'आजच्या योजनेत {count} विषय',
  'recommendations.planTopicsMany': 'आजच्या योजनेत {count} विषय',
  'recommendations.viewProgress': 'प्रगती पाहा →',
  'recommendations.viewLearningPath': 'शिक्षण मार्ग पाहा →',
  'recommendations.emptyDescription':
    'अजून सूचना नाहीत — काही असाइनमेंट प्रश्नांची उत्तरे द्या आणि आम्ही तुम्हाला पुन्हा पाहण्यासारखे अध्याय सुचवू.',

  // ── AI explanation chrome ────────────────────────────────────────────
  // `explanation.regenerateInLocale` / `.regenerating` are intentionally
  // omitted: AI content for mr falls back to English (LA-9d), so the
  // "re-explain in this language" affordance never applies — it stays English.
  'explanation.cta': '✨ हे उत्तर समजावून सांगा',
  'explanation.whyRight': 'हे उत्तर का बरोबर आहे',
  'explanation.whereWrong': 'इथे काय चुकले',
  'explanation.writing': 'तुमचे स्पष्टीकरण लिहित आहे…',
  'explanation.error': 'आत्ता स्पष्टीकरण मिळू शकले नाही. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.',
  'explanation.retry': 'पुन्हा प्रयत्न करा',
  'explanation.stubNote':
    'AI मॉडेलशिवाय तयार केले — AI कॉन्फिगर केल्यावर स्पष्टीकरणे अधिक चांगली होतील.',

  // ── Activity streak ──────────────────────────────────────────────────
  'streak.days': '{count} दिवसांची मालिका',
  'streak.tierStarter': 'जोरात',
  'streak.tierWeek': 'आठवड्याचा शिलेदार',
  'streak.tierMonth': 'महिन्याचा मास्टर',
  'streak.tierChampion': 'चॅम्पियन',
  'streak.best': 'सर्वोत्तम: {count}',
  'streak.grace': 'सवलत ✓',
  'streak.graceTitle': 'सवलतीचा दिवस वापरला — एक दिवस चुकूनही मालिका टिकवली',

  // ── Parent dashboard (LA-9d) ─────────────────────────────────────────
  'parent.title': 'पालक डॅशबोर्ड',
  'parent.description': 'तुमच्या मुलांची शिकण्याची प्रगती पाहा.',
  'parent.noChildrenTitle': 'तुमच्या खात्याशी कोणतेही मूल जोडलेले नाही',
  'parent.noChildrenDescription': 'तुमच्या मुलांची खाती जोडण्यासाठी शाळेच्या प्रशासकाला सांगा.',
  'parent.gradeShort': 'इ.{grade}',
  'parent.grade': 'इयत्ता {grade}',
  'parent.overview': '{name} चा आढावा',
  'parent.viewInsights': 'माहिती पाहा →',
  'parent.tabProgress': 'प्रगती',
  'parent.tabAssignments': 'असाइनमेंट्स',
  'parent.noProgressTitle': 'अजून प्रगती नाही',
  'parent.noProgressDescription': '{name} ने अजून कोणतीही असाइनमेंट सादर केलेली नाही.',
  'parent.noAssignmentsDescription': 'शिक्षकांनी असाइनमेंट तयार केल्यावर त्या इथे दिसतील.',
  'parent.questionsPractisedOne': '{count} प्रश्नाचा सराव केला',
  'parent.questionsPractisedMany': '{count} प्रश्नांचा सराव केला',
  'parent.statusSubmitted': 'सादर केले',
  'parent.statusOverdue': 'मुदत संपलेली',
  'parent.statusPending': 'प्रलंबित',
  'parent.overdueOn': 'मुदत संपली — {date}',
  'parent.dueOn': 'मुदत {date}',

  // ── Connectivity (PWA offline indicator) — core-loop string ──────────
  'connectivity.offlineTitle': 'तुम्ही ऑफलाइन आहात',
  'connectivity.offlineBanner': 'तुम्ही ऑफलाइन आहात — जतन केलेले काम दाखवत आहोत.',
  'connectivity.backOnline': 'पुन्हा ऑनलाइन.',
} satisfies Partial<LocaleDict>;
