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

  // ── Teacher dashboard + insight panels ───────────────────────────────
  'teacher.title': 'शिक्षक डैशबोर्ड',
  'teacher.subtitle': 'आपके रूम, प्रॉब्लम सेट और असाइनमेंट — सब एक जगह।',
  'teacher.aiGrading': '✨ AI जाँच',
  'teacher.newQuestion': '+ प्रश्न',
  'teacher.newProblemSet': '+ प्रॉब्लम सेट',
  'teacher.newAssignment': '+ असाइनमेंट',
  'teacher.statRooms': 'विषय रूम',
  'teacher.statStudents': 'विद्यार्थी',
  'teacher.statProblemSets': 'प्रॉब्लम सेट',
  'teacher.statOpenAssignments': 'खुले असाइनमेंट',
  'teacher.noRoomsTitle': 'अभी कोई विषय रूम नहीं',
  'teacher.noRoomsDescription': 'क्लासरूम से जुड़ने के लिए एडमिन से कहें।',
  'teacher.studentsCountOne': '{count} विद्यार्थी',
  'teacher.studentsCountMany': '{count} विद्यार्थी',
  'teacher.assign': 'असाइन करें',
  'teacher.viewInsights': 'क्लास इनसाइट्स देखें',
  'teacher.hideInsights': 'क्लास इनसाइट्स छिपाएँ',
  'teacher.newSetAction': '+ नया सेट',
  'teacher.noSetsTitle': 'अभी कोई प्रॉब्लम सेट नहीं',
  'teacher.noSetsDescription': 'प्रश्नों का ऐसा सेट बनाएँ जिसे आप किसी भी रूम को असाइन कर सकें।',
  'teacher.buildSet': 'प्रॉब्लम सेट बनाएँ',
  'teacher.questionsCountOne': '{count} प्रश्न',
  'teacher.questionsCountMany': '{count} प्रश्न',
  'teacher.minutesApprox': '~{minutes} मिनट',
  'teacher.previewAsStudent': 'विद्यार्थी की नज़र से देखें',
  'teacher.sectionJoinCodes': 'क्लास जॉइन कोड',
  'teacher.joinCodesDescription': 'कोड साझा करें ताकि विद्यार्थी खुद क्लासरूम से जुड़ सकें।',
  'teacher.sectionAssignments': 'असाइनमेंट',
  'teacher.noAssignmentsDescription': 'सबमिशन ट्रैक करने के लिए पहला असाइनमेंट बनाएँ।',
  'teacher.createAssignment': 'असाइनमेंट बनाएँ',
  'teacher.submittedRatio': '{submitted}/{total} जमा हुए',
  'teacher.avgScore': 'औसत: {pct}%',

  // Needs-attention strip
  'teacher.needsAttention': 'ध्यान दें · {count}',
  'teacher.bucketOverdue': '{count} समय पार',
  'teacher.bucketUngraded': '{count} बिना जाँचे',
  'teacher.bucketLowCompletion': '{count} कम सबमिशन',

  // Class health panel
  'teacher.classHealth': 'क्लास की सेहत',
  'teacher.loadingClassHealth': 'क्लास की सेहत का डेटा लोड हो रहा है…',
  'teacher.noClassHealth':
    'अभी क्लास की सेहत का डेटा नहीं। विद्यार्थियों के असाइनमेंट पूरे करने पर इनसाइट्स दिखेंगी।',
  'teacher.computing': 'गणना हो रही है…',
  'teacher.refresh': 'रीफ़्रेश करें',
  'teacher.refreshing': 'रीफ़्रेश हो रहा है…',
  'teacher.thChapter': 'अध्याय',
  'teacher.thAvg': 'औसत',
  'teacher.thStruggling': 'अटक रहे',
  'teacher.thStatus': 'स्थिति',
  'teacher.statusStruggling': 'अटक रहे',
  'teacher.statusAtRisk': 'जोखिम में',
  'teacher.statusProficient': 'निपुण',
  'teacher.lastUpdated': 'आख़िरी अपडेट: {datetime}',

  // Weekly AI summary panel
  'teacher.weeklySummary': 'साप्ताहिक AI समरी',
  'teacher.weeklyLoadError': 'अभी साप्ताहिक समरी लोड नहीं हो पाई।',
  'teacher.noWeeklySummary': 'अभी कोई साप्ताहिक समरी नहीं। इस हफ़्ते की अभ्यास गतिविधि से एक बनाएँ।',
  'teacher.generating': 'बन रही है…',
  'teacher.generate': 'बनाएँ',
  'teacher.weeklyGenError': 'अभी समरी नहीं बन पाई। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.weekOf': '{start} – {end} का सप्ताह',
  'teacher.stubSummaryNote': 'AI उपलब्ध नहीं था, इसलिए यह सीधे आपकी क्लास के डेटा से बनी है।',
  'teacher.practisedRatio': '{active}/{total} ने अभ्यास किया',
  'teacher.avgPct': '{pct}% औसत',
  'teacher.needsWork': 'मेहनत चाहिए:',
  'teacher.strong': 'मज़बूत:',
  'teacher.generatedOn': '{date} को बनी',
  'teacher.regenerating': 'फिर बन रही है…',
  'teacher.regenerate': 'फिर बनाएँ',

  // Interventions panel
  'teacher.interventions': 'मदद के सुझाव',
  'teacher.weakChaptersOne': '{count} कमज़ोर अध्याय',
  'teacher.weakChaptersMany': '{count} कमज़ोर अध्याय',
  'teacher.priority': 'प्राथमिकता {n}',
  'teacher.stubStrategyNote':
    'AI उपलब्ध नहीं था, इसलिए यह रणनीति सीधे {name} के लर्निंग-गैप डेटा से बनी है।',
  'teacher.recurringMisconception': 'दोहराई जा रही ग़लतफ़हमी:',
  'teacher.dismiss': 'हटाएँ',
  'teacher.markPlanned': 'योजना में जोड़ें',
  'teacher.planned': 'योजना में',
  'teacher.dismissed': 'हटाया गया',
  'teacher.resolve': 'पूरा हुआ',
  'teacher.interventionsLoadError': 'अभी सुझाव लोड नहीं हो पाए।',
  'teacher.noInterventions':
    'अभी कोई अटकता विद्यार्थी चिह्नित नहीं। मौजूदा लर्निंग-गैप डेटा से सुझाव बनाएँ।',
  'teacher.interventionsGenError': 'अभी सुझाव नहीं बन पाए। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.interventionsFootnote': 'AI रणनीतियाँ आपके फ़ॉलो-अप में मदद करती हैं — नियंत्रण आपके पास है।',

  // Misconception clusters panel
  'teacher.misconceptions': 'क्लास की ग़लतफ़हमियाँ',
  'teacher.tryInClass': 'क्लास में आज़माएँ:',
  'teacher.seenTimesOne': '{count} बार दिखी · आख़िरी बार {last} · अपडेट {updated}',
  'teacher.seenTimesMany': '{count} बार दिखी · आख़िरी बार {last} · अपडेट {updated}',
  'teacher.misconceptionsLoadError': 'अभी ग़लतफ़हमी पैटर्न लोड नहीं हो पाए।',
  'teacher.noMisconceptions':
    'अभी कोई ग़लतफ़हमी पैटर्न नहीं मिला — इस क्लास में कुछ असाइनमेंट जँचने के बाद वे दिखेंगे।',
  'teacher.refreshError': 'अभी रीफ़्रेश नहीं हो पाया। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.recomputing': 'हाल के सबमिशन से दोबारा गणना हो रही है — नए पैटर्न जल्द यहाँ दिखेंगे।',
  'teacher.misconceptionsFootnote': 'पूरी क्लास के पैटर्न — एक बार समझाएँ, सबकी मदद करें।',

  // AI assignment drafts panel
  'teacher.aiDrafts': 'AI असाइनमेंट ड्राफ़्ट',
  'teacher.draftPending': 'आपकी क्लास के कमज़ोर हिस्सों से ड्राफ़्ट बन रहा है…',
  'teacher.draftPendingNote': 'इसमें आमतौर पर कुछ सेकंड लगते हैं।',
  'teacher.draftFailed': 'यह ड्राफ़्ट नहीं बन पाया।',
  'teacher.retrying': 'फिर कोशिश हो रही है…',
  'teacher.tryAgain': 'फिर कोशिश करें',
  'teacher.practiceSetDefault': 'अभ्यास सेट',
  'teacher.assigned': 'असाइन हो गया',
  'teacher.viewAssignment': 'असाइनमेंट देखें',
  'teacher.classCanSee': 'आपकी क्लास इसे अब देख सकती है।',
  'teacher.stubDraftNote':
    'AI उपलब्ध नहीं था, इसलिए यह ड्राफ़्ट सीधे आपकी क्लास के अभ्यास डेटा से बना है।',
  'teacher.dismissDraftError': 'अभी ड्राफ़्ट नहीं हटा। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.approveEllipsis': 'स्वीकृत करें…',
  'teacher.dueDate': 'अंतिम तिथि',
  'teacher.titleLabel': 'शीर्षक',
  'teacher.titleOptionalHint': '(वैकल्पिक — खाली छोड़ने पर ड्राफ़्ट का शीर्षक रहेगा)',
  'teacher.approveError': 'अभी ड्राफ़्ट स्वीकृत नहीं हो पाया। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.useTryAgainHint': 'नया ड्राफ़्ट बनाने के लिए "फिर कोशिश करें" दबाएँ।',
  'teacher.assigning': 'असाइन हो रहा है…',
  'teacher.assignToClass': 'क्लास को असाइन करें',
  'teacher.draftsLoadError': 'अभी ड्राफ़्ट लोड नहीं हो पाए।',
  'teacher.noDrafts':
    'अभी कोई ड्राफ़्ट नहीं — AI को इस क्लास के सबसे कमज़ोर अध्यायों से अभ्यास सेट बनाने दें, फिर देखकर असाइन करें।',
  'teacher.draftStartError': 'अभी ड्राफ़्ट शुरू नहीं हो पाया। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.questionsLabel': 'प्रश्न',
  'teacher.difficultyLabel': 'कठिनाई',
  'teacher.starting': 'शुरू हो रहा है…',
  'teacher.draftAssignment': 'असाइनमेंट ड्राफ़्ट करें',
  'teacher.aiProposesFootnote':
    'AI सुझाता है, फ़ैसला आपका — आपकी स्वीकृति से पहले कुछ भी विद्यार्थियों तक नहीं पहुँचता।',

  // Question quality panel
  'teacher.questionQuality': 'प्रश्न गुणवत्ता',
  'teacher.flagTooHard': 'लगभग किसी ने सही नहीं किया — शब्दांकन या दर्ज सही उत्तर जाँचें।',
  'teacher.flagTooEasy': 'लगभग सबने सही किया — सेट में इसका योगदान कम है।',
  'teacher.flagMislabeled': 'यह अपने तय कठिनाई स्तर से ज़्यादा कठिन या आसान चल रहा है।',
  'teacher.flagLowDiscrimination':
    'तेज़ विद्यार्थियों ने भी बेहतर नहीं किया — अक्सर गलत दर्ज उत्तर का संकेत।',
  'teacher.flagOk': 'जैसा तय था वैसा ही चल रहा है।',
  'teacher.questionFallback': 'प्रश्न #{id}',
  'teacher.correctPct': '{pct} सही',
  'teacher.authoredDifficulty': 'तय कठिनाई',
  'teacher.observedDifficulty': 'देखी गई कठिनाई',
  'teacher.harderThanLabelled': 'लेबल से कठिन',
  'teacher.easierThanLabelled': 'लेबल से आसान',
  'teacher.discrimination': 'विभेदन',
  'teacher.calibrationSummaryOne': '{total} में से {flagged} कैलिब्रेटेड प्रश्न पर नज़र चाहिए।',
  'teacher.calibrationSummaryMany': '{total} में से {flagged} कैलिब्रेटेड प्रश्नों पर नज़र चाहिए।',
  'teacher.qualityLoadError': 'अभी प्रश्न विश्लेषण लोड नहीं हो पाया।',
  'teacher.noFlagged':
    'अभी कोई प्रश्न चिह्नित नहीं। कैलिब्रेशन के लिए हर प्रश्न पर कुछ प्रयास चाहिए — क्लास के अभ्यास के बाद रीफ़्रेश करें।',
  'teacher.recalibrateStartError': 'अभी रीकैलिब्रेशन शुरू नहीं हो पाया। कृपया थोड़ी देर में फिर कोशिश करें।',
  'teacher.recalibrating': 'हाल के उत्तरों से रीकैलिब्रेशन हो रहा है — नए नतीजे जल्द यहाँ दिखेंगे।',
  'teacher.qualityFootnote': 'नतीजे आपकी क्लास के असली उत्तरों से आते हैं — AI का अनुमान नहीं।',
  'teacher.calibrate': 'कैलिब्रेट करें',

  // Classroom join-code widget
  'teacher.joinCodeHeading': 'क्लासरूम जॉइन कोड',
  'teacher.copied': 'कॉपी हो गया!',
  'teacher.copyCode': 'कोड कॉपी करें',
  'teacher.copyLink': 'लिंक कॉपी करें',
  'teacher.noExpiry': 'कोई समय-सीमा नहीं',
  'teacher.expired': 'समय-सीमा बीत गई',
  'teacher.expiresInUnderHour': '1 घंटे से कम में खत्म',
  'teacher.expiresInHours': '{hours} घंटे में खत्म',
  'teacher.expiresInDays': '{days} दिन में खत्म',
  'teacher.regenerateWarning':
    'दोबारा बनाने पर मौजूदा कोड बेकार हो जाएगा। जो विद्यार्थी अभी नहीं जुड़े, उन्हें नया कोड चाहिए होगा।',
  'teacher.yesRegenerate': 'हाँ, दोबारा बनाएँ',
  'teacher.generateJoinCode': 'जॉइन कोड बनाएँ',

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
