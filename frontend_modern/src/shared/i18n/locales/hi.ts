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

  // ── Home (marketing) page ────────────────────────────────────────────
  'home.login': 'लॉग इन करें',
  'home.loginArrow': 'लॉग इन करें →',
  'home.heroTitle': 'हर बच्चे की क्षमता को खोलिए।',
  'home.heroSubtitle':
    'गणित और विज्ञान के लिए अनुकूली शिक्षा और शैक्षिक एनालिटिक्स — विद्यार्थियों के लिए मुफ़्त, और उनका मार्गदर्शन करने वाले शिक्षकों, अभिभावकों और स्कूलों के लिए बनाया गया।',
  'home.startFree': 'विद्यार्थी के रूप में मुफ़्त शुरू करें',
  'home.pillarPracticeTitle': 'अभ्यास',
  'home.pillarPracticeDesc':
    'गणित और विज्ञान में असीमित, अपने-आप बनने वाले प्रश्न — किन्हीं दो विद्यार्थियों को एक जैसा पेपर नहीं मिलता।',
  'home.pillarEvaluateTitle': 'जाँच',
  'home.pillarEvaluateDesc':
    'हर उत्तर की जाँच अपने-आप और तुरंत होती है — शिक्षकों के लिए दोहराव वाली कॉपी-जाँच नहीं।',
  'home.pillarAnalyseTitle': 'विश्लेषण',
  'home.pillarAnalyseDesc':
    'उन्नत एनालिटिक्स हर बच्चे की मज़बूतियाँ, कमियाँ और आगे क्या अभ्यास करना है, सामने लाती है।',
  'home.missionKicker': 'हमारा मिशन',
  'home.missionTitle':
    'गणित और विज्ञान का अभ्यास हर विद्यार्थी के लिए सचमुच रोचक बनाना।',
  'home.missionBody1':
    'OpenShiksha एक लर्निंग प्लेटफ़ॉर्म है जो अवधारणाओं की पकड़ और सीखने के परिणाम बेहतर करने के लिए बना है। हम कक्षा 7–10 का गणित और विज्ञान कवर करते हैं, कक्षा 1 से रिफ़्रेशर के साथ — सब CBSE बोर्ड के अनुरूप और English व हिंदी में उपलब्ध।',
  'home.missionOpenPre': 'हमारा',
  'home.missionOpenTerm': 'ओपन मॉडल',
  'home.missionOpenPost': 'किसी भी विद्यार्थी को मुफ़्त साइन अप करके सीखने देता है। हमारा',
  'home.missionPartnerTerm': 'पार्टनरशिप मॉडल',
  'home.missionPartnerPost':
    'स्कूलों और शैक्षिक संस्थाओं को वर्चुअल क्लासरूम चलाने और डेटा-आधारित निर्णय लेने के डैशबोर्ड देता है।',
  'home.teacherAlt': 'विद्यार्थियों की मदद करते हुए एक शिक्षक',
  'home.startNowTitle': 'अभी शुरू करें',
  'home.startNowSubtitle':
    'विद्यार्थियों के लिए हमेशा मुफ़्त। स्कूलों और शैक्षिक संस्थाओं के लिए मार्गदर्शित शुरुआत।',
  'home.studentsCardTitle': 'विद्यार्थी',
  'home.studentsCardDesc': 'मुफ़्त खाता बनाएँ और आज ही अभ्यास शुरू करें।',
  'home.studentsCardCta': 'मुफ़्त साइन अप करें →',
  'home.schoolsCardTitle': 'स्कूल और संस्थाएँ',
  'home.schoolsCardDesc': 'OpenShiksha को अपनी कक्षाओं तक लाएँ।',
  'home.schoolsCardCta': 'पूछताछ करें →',
  'home.featuresTitle': 'मुख्य विशेषताएँ',
  'home.feature1':
    'उन्नत एनालिटिक्स मज़बूतियाँ, कमज़ोरियाँ और ध्यान माँगती अवधारणाएँ ठीक-ठीक बताती है।',
  'home.feature2': 'व्यक्तिगत फ़ीडबैक हर विद्यार्थी के खास लर्निंग आउटकम पर केंद्रित होता है।',
  'home.feature3':
    'फ़ॉर्मूला-आधारित टेम्पलेट लगभग असीमित प्रश्न बनाते हैं — भरपूर अभ्यास, नकल नहीं।',
  'home.feature4': 'स्वचालित जाँच शिक्षकों की घंटों की दोहराव वाली कॉपी-जाँच हटा देती है।',
  'home.feature5':
    'साप्ताहिक AI सारांश वाला अभिभावक डैशबोर्ड परिवारों को जोड़े रखता है।',
  'home.feature6': 'कम कीमत के मोबाइल और टैबलेट पर भी बढ़िया चलता है — English और हिंदी में।',
  'home.footerSchools': 'स्कूलों के लिए',

  // ── Registration pages ───────────────────────────────────────────────
  'register.title': 'अपना खाता बनाएँ',
  'register.subtitle': 'आप कैसे सीखना चाहेंगे?',
  'register.haveAccount': 'पहले से खाता है?',
  'register.signIn': 'साइन इन करें',
  'register.back': '← वापस',
  'register.joinSchoolTitle': 'स्कूल से जुड़ें',
  'register.joinSchoolDesc':
    'अपने शिक्षक से मिला क्लासरूम जॉइन कोड इस्तेमाल करें — दाखिला अपने-आप हो जाएगा।',
  'register.openTitle': 'अपने दम पर पढ़ें',
  'register.openDesc':
    'साझा प्रश्न बैंक से अपनी गति से अभ्यास करें — स्कूल की ज़रूरत नहीं।',
  'register.openSubtitle': 'साझा प्रश्न बैंक मुफ़्त में इस्तेमाल करें।',
  'register.schoolTitle': 'अपने स्कूल से जुड़ें',
  'register.schoolSubtitle': 'अपने शिक्षक से मिला जॉइन कोड डालें।',
  'register.firstName': 'पहला नाम',
  'register.lastName': 'उपनाम',
  'register.username': 'यूज़रनेम',
  'register.password': 'पासवर्ड',
  'register.emailOptional': 'ईमेल (वैकल्पिक)',
  'register.joinCode': 'क्लासरूम जॉइन कोड',
  'register.joinCodePlaceholder': 'जैसे ABC123',
  'register.error': 'रजिस्ट्रेशन नहीं हो पाया। कृपया फिर कोशिश करें।',
  'register.creating': 'खाता बन रहा है…',
  'register.startPractising': 'अभ्यास शुरू करें',
  'register.createAccount': 'खाता बनाएँ',

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

  // ── Parent dashboard ─────────────────────────────────────────────────
  'parent.title': 'अभिभावक डैशबोर्ड',
  'parent.description': 'अपने बच्चों की पढ़ाई की प्रगति देखें।',
  'parent.noChildrenTitle': 'आपके खाते से कोई बच्चा नहीं जुड़ा है',
  'parent.noChildrenDescription': 'अपने बच्चों के खाते जोड़ने के लिए स्कूल एडमिन से कहें।',
  'parent.gradeShort': 'कक्षा {grade}',
  'parent.grade': 'कक्षा {grade}',
  'parent.overview': '{name} की प्रगति-झलक',
  'parent.viewInsights': 'इनसाइट्स देखें →',
  'parent.tabProgress': 'प्रगति',
  'parent.tabAssignments': 'असाइनमेंट',
  'parent.noProgressTitle': 'अभी कोई प्रगति नहीं',
  'parent.noProgressDescription': '{name} ने अभी तक कोई असाइनमेंट जमा नहीं किया है।',
  'parent.noAssignmentsDescription': 'शिक्षक के असाइनमेंट बनाते ही वे यहाँ दिखेंगे।',
  'parent.questionsPractisedOne': '{count} प्रश्न का अभ्यास हुआ',
  'parent.questionsPractisedMany': '{count} प्रश्नों का अभ्यास हुआ',
  'parent.statusSubmitted': 'जमा हो गया',
  'parent.statusOverdue': 'समय निकल गया',
  'parent.statusPending': 'बाकी है',
  'parent.overdueOn': 'समय निकल गया — {date}',
  'parent.dueOn': 'अंतिम तिथि {date}',

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
