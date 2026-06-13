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
  'common.cancel': 'Cancel',
  'common.practice': 'Practice',
  'common.topicsOne': '{count} topic',
  'common.topicsMany': '{count} topics',

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

  // ── Home (marketing) page ────────────────────────────────────────────
  'home.login': 'Log in',
  'home.loginArrow': 'Log in →',
  'home.heroTitle': 'Unlock every child’s potential.',
  'home.heroSubtitle':
    'Adaptive learning and educational analytics for Maths & Science — free for students, and built for the teachers, parents, and schools who guide them.',
  'home.startFree': 'Start free as a student',
  'home.pillarPracticeTitle': 'Practice',
  'home.pillarPracticeDesc':
    'Unlimited, auto-generated questions in Maths & Science — no two students get the same paper.',
  'home.pillarEvaluateTitle': 'Evaluate',
  'home.pillarEvaluateDesc':
    'Every answer is corrected automatically and instantly — no repetitive marking for teachers.',
  'home.pillarAnalyseTitle': 'Analyse',
  'home.pillarAnalyseDesc':
    'Advanced analytics surface each child’s strengths, gaps, and what to practise next.',
  'home.missionKicker': 'Our mission',
  'home.missionTitle':
    'Make practising Maths & Science genuinely engaging — for every student.',
  'home.missionBody1':
    'OpenShiksha is a learning platform built to improve concept retention and learning outcomes. We cover classes 7–10 Maths and Science, with refreshers from class 1, all aligned to the CBSE board and available in English and Hindi.',
  'home.missionOpenPre': 'Our',
  'home.missionOpenTerm': 'Open Model',
  'home.missionOpenPost': 'lets any student sign up and learn for free. Our',
  'home.missionPartnerTerm': 'Partnership Model',
  'home.missionPartnerPost':
    'gives schools and educational organisations the dashboards to run virtual classrooms and make data-driven decisions.',
  'home.teacherAlt': 'A teacher helping students',
  'home.startNowTitle': 'Start now',
  'home.startNowSubtitle':
    'Free for students, forever. A guided onboarding for schools and educational organisations.',
  'home.studentsCardTitle': 'Students',
  'home.studentsCardDesc': 'Create a free account and start practising today.',
  'home.studentsCardCta': 'Sign up free →',
  'home.schoolsCardTitle': 'Schools & organisations',
  'home.schoolsCardDesc': 'Bring OpenShiksha to your classrooms.',
  'home.schoolsCardCta': 'Enquire →',
  'home.featuresTitle': 'Key features',
  'home.feature1':
    'Advanced analytics pinpoint strengths, weaknesses, and concepts that need attention.',
  'home.feature2': 'Personalised feedback targets each student’s specific learning outcomes.',
  'home.feature3':
    'Formulaic templates generate near-infinite questions — unlimited practice, no copying.',
  'home.feature4': 'Automated correction removes hours of repetitive marking for teachers.',
  'home.feature5':
    'A dedicated parent dashboard with weekly AI summaries keeps families engaged.',
  'home.feature6': 'Works beautifully on low-cost mobiles and tablets, in English and Hindi.',
  'home.footerSchools': 'For schools',

  // ── Registration pages ───────────────────────────────────────────────
  'register.title': 'Create your account',
  'register.subtitle': 'How would you like to learn?',
  'register.haveAccount': 'Already have an account?',
  'register.signIn': 'Sign in',
  'register.back': '← Back',
  'register.joinSchoolTitle': 'Join a school',
  'register.joinSchoolDesc':
    'Use a classroom join code from your teacher to enroll automatically.',
  'register.openTitle': 'Study independently',
  'register.openDesc':
    'Practice from the shared question bank at your own pace — no school needed.',
  'register.openSubtitle': 'Access the shared question bank for free.',
  'register.schoolTitle': 'Join your school',
  'register.schoolSubtitle': 'Enter the join code from your teacher.',
  'register.firstName': 'First name',
  'register.lastName': 'Last name',
  'register.username': 'Username',
  'register.password': 'Password',
  'register.emailOptional': 'Email (optional)',
  'register.joinCode': 'Classroom join code',
  'register.joinCodePlaceholder': 'e.g. ABC123',
  'register.error': 'Registration failed. Please try again.',
  'register.creating': 'Creating account…',
  'register.startPractising': 'Start practising',
  'register.createAccount': 'Create account',

  // ── Student dashboard ────────────────────────────────────────────────
  'dashboard.greeting': 'Hi, {name}!',
  'dashboard.title': 'Your dashboard',
  'dashboard.subtitle': 'Here are your assignments.',
  'dashboard.myProgress': 'My progress →',
  'dashboard.loadError': 'Failed to load assignments. Please refresh the page.',
  'dashboard.openEmptyTitle': "You're not enrolled in a classroom yet",
  'dashboard.openEmptyDescription':
    'Browse the shared question bank to start practising on your own.',
  'dashboard.browseSubjects': 'Browse subjects →',

  // ── Assignment list (sections + empty state) ─────────────────────────
  'assignments.emptyTitle': 'No assignments yet',
  'assignments.emptyDescription': 'Your teacher will assign some soon. Check back later!',
  'assignments.sectionOverdue': 'Overdue',
  'assignments.sectionDueSoon': 'Due Soon',
  'assignments.sectionUpcoming': 'Upcoming',
  'assignments.sectionCompleted': 'Completed',

  // ── Assignment card ──────────────────────────────────────────────────
  'assignment.overdueBy': 'Overdue by {distance}',
  'assignment.dueIn': 'Due {distance}',
  'assignment.submittedAgo': 'Submitted {distance}',
  'assignment.submitted': 'Submitted',
  'assignment.remedialBadge': 'Remedial Practice',
  'assignment.progress': 'Progress',
  'assignment.ctaReview': 'Review',
  'assignment.ctaContinue': 'Continue',
  'assignment.ctaStart': 'Start',

  // ── Assignment detail (work + submit flow) ───────────────────────────
  'assignmentDetail.back': 'Back to assignments',
  'assignmentDetail.answeredCount': '{answered} of {total} answered',
  'assignmentDetail.submittedNice': 'Assignment submitted — nice work!',
  'assignmentDetail.submittedTitle': 'Submitted',
  'assignmentDetail.grading': 'Grading in progress…',
  'assignmentDetail.notFoundTitle': 'Assignment not found',
  'assignmentDetail.notFoundDescription': "It may have been removed or you don't have access.",
  'assignmentDetail.backToDashboard': 'Back to dashboard',
  'assignmentDetail.noQuestions': 'No questions in this assignment',
  'assignmentDetail.submit': 'Submit assignment',
  'assignmentDetail.confirmTitle': 'Submit assignment?',
  'assignmentDetail.confirmBody':
    'You have answered {answered} of {total} questions. You cannot change your answers after submitting.',
  'assignmentDetail.confirmSubmit': 'Submit',
  'assignmentDetail.submitting': 'Submitting…',

  // ── Due for Review panel (SRS) ───────────────────────────────────────
  'dueReview.title': 'Due for Review',
  'dueReview.overdueCount': '{count} overdue',
  'dueReview.statusOverdue': 'Overdue',
  'dueReview.statusToday': 'Due today',
  'dueReview.statusSoon': 'Coming up',
  'dueReview.overdueSince': 'Overdue since {date}',
  'dueReview.dueOn': 'Due {date}',
  'dueReview.interval': 'every {days}d',
  'dueReview.reviewedTimes': '{count}× reviewed',
  'dueReview.moreTopics': '+{count} more topics',
  'dueReview.emptyDescription':
    'Nothing due yet — finish a few assignments and your review schedule will appear here.',
  'dueReview.footer': 'Practice your assignments to push review dates forward.',

  // ── Recommendations panel ────────────────────────────────────────────
  'recommendations.title': 'What to Practice Next',
  'recommendations.todaysPlan': "Today's plan: ~{minutes} min",
  'recommendations.yourScore': 'your score',
  'recommendations.planTopicsOne': '{count} topic in today’s plan',
  'recommendations.planTopicsMany': '{count} topics in today’s plan',
  'recommendations.viewProgress': 'View progress →',
  'recommendations.viewLearningPath': 'View learning path →',
  'recommendations.emptyDescription':
    "No suggestions yet — answer a few assignment questions and we'll point you to the chapters worth revisiting.",

  // ── Explanation panel (AI) ───────────────────────────────────────────
  'explanation.cta': '✨ Explain this answer',
  'explanation.whyRight': 'Why this answer is right',
  'explanation.whereWrong': 'Where this went wrong',
  'explanation.writing': 'Writing your explanation…',
  'explanation.error': "Couldn't fetch an explanation just now. Please try again in a moment.",
  'explanation.retry': 'Retry',
  'explanation.stubNote':
    'Generated without an AI model — explanations get richer once AI is configured.',
  'explanation.regenerateInLocale': 'Explain in English',
  'explanation.regenerating': 'Rewriting…',

  // ── Parent dashboard ─────────────────────────────────────────────────
  'parent.title': 'Parent Dashboard',
  'parent.description': "Monitor your children's learning progress.",
  'parent.noChildrenTitle': 'No children linked to your account',
  'parent.noChildrenDescription': "Ask the school admin to link your children's accounts.",
  'parent.gradeShort': 'Gr.{grade}',
  'parent.grade': 'Grade {grade}',
  'parent.overview': "{name}'s Overview",
  'parent.viewInsights': 'View Insights →',
  'parent.tabProgress': 'Progress',
  'parent.tabAssignments': 'Assignments',
  'parent.noProgressTitle': 'No progress yet',
  'parent.noProgressDescription': "{name} hasn't submitted any assignments yet.",
  'parent.noAssignmentsDescription':
    'Assignments will appear here once the teacher creates them.',
  'parent.questionsPractisedOne': '{count} question practised',
  'parent.questionsPractisedMany': '{count} questions practised',
  'parent.statusSubmitted': 'Submitted',
  'parent.statusOverdue': 'Overdue',
  'parent.statusPending': 'Pending',
  'parent.overdueOn': 'Overdue — {date}',
  'parent.dueOn': 'Due {date}',

  // ── Teacher dashboard + insight panels ───────────────────────────────
  'teacher.title': 'Teacher dashboard',
  'teacher.subtitle': 'Your rooms, problem sets, and assignments in one place.',
  'teacher.aiGrading': '✨ AI grading',
  'teacher.newQuestion': '+ Question',
  'teacher.newProblemSet': '+ Problem set',
  'teacher.newAssignment': '+ Assignment',
  'teacher.statRooms': 'Subject rooms',
  'teacher.statStudents': 'Students',
  'teacher.statProblemSets': 'Problem sets',
  'teacher.statOpenAssignments': 'Open assignments',
  'teacher.noRoomsTitle': 'No subject rooms yet',
  'teacher.noRoomsDescription': 'Ask an admin to assign you to a classroom.',
  'teacher.studentsCountOne': '{count} student',
  'teacher.studentsCountMany': '{count} students',
  'teacher.assign': 'Assign',
  'teacher.viewInsights': 'View class insights',
  'teacher.hideInsights': 'Hide class insights',
  'teacher.newSetAction': '+ New set',
  'teacher.noSetsTitle': 'No problem sets yet',
  'teacher.noSetsDescription': 'Build a set of questions you can assign to any of your rooms.',
  'teacher.buildSet': 'Build a problem set',
  'teacher.questionsCountOne': '{count} question',
  'teacher.questionsCountMany': '{count} questions',
  'teacher.minutesApprox': '~{minutes} min',
  'teacher.previewAsStudent': 'Preview as student',
  'teacher.sectionJoinCodes': 'Class join codes',
  'teacher.joinCodesDescription': 'Share a code so students can join the classroom themselves.',
  'teacher.sectionAssignments': 'Assignments',
  'teacher.noAssignmentsDescription': 'Create your first assignment to start tracking submissions.',
  'teacher.createAssignment': 'Create assignment',
  'teacher.submittedRatio': '{submitted}/{total} submitted',
  'teacher.avgScore': 'Avg: {pct}%',

  // Needs-attention strip
  'teacher.needsAttention': 'Needs attention · {count}',
  'teacher.bucketOverdue': '{count} overdue',
  'teacher.bucketUngraded': '{count} ungraded',
  'teacher.bucketLowCompletion': '{count} low completion',

  // Class health panel
  'teacher.classHealth': 'Class Health',
  'teacher.loadingClassHealth': 'Loading class health data…',
  'teacher.noClassHealth':
    'No class health data yet. Insights appear after students complete assignments.',
  'teacher.computing': 'Computing…',
  'teacher.refresh': 'Refresh',
  'teacher.refreshing': 'Refreshing…',
  'teacher.thChapter': 'Chapter',
  'teacher.thAvg': 'Avg',
  'teacher.thStruggling': 'Struggling',
  'teacher.thStatus': 'Status',
  'teacher.statusStruggling': 'Struggling',
  'teacher.statusAtRisk': 'At Risk',
  'teacher.statusProficient': 'Proficient',
  'teacher.lastUpdated': 'Last updated: {datetime}',

  // Weekly AI summary panel
  'teacher.weeklySummary': 'Weekly AI Summary',
  'teacher.weeklyLoadError': "Couldn't load the weekly summary just now.",
  'teacher.noWeeklySummary': "No weekly summary yet. Generate one from this week's practice activity.",
  'teacher.generating': 'Generating…',
  'teacher.generate': 'Generate',
  'teacher.weeklyGenError': "Couldn't generate the summary just now. Please try again in a moment.",
  'teacher.weekOf': 'Week of {start} – {end}',
  'teacher.stubSummaryNote': 'AI was unavailable, so this was built directly from your class data.',
  'teacher.practisedRatio': '{active}/{total} practised',
  'teacher.avgPct': '{pct}% avg',
  'teacher.needsWork': 'Needs work:',
  'teacher.strong': 'Strong:',
  'teacher.generatedOn': 'Generated {date}',
  'teacher.regenerating': 'Regenerating…',
  'teacher.regenerate': 'Regenerate',

  // Interventions panel
  'teacher.interventions': 'Intervention Suggestions',
  'teacher.weakChaptersOne': '{count} weak chapter',
  'teacher.weakChaptersMany': '{count} weak chapters',
  'teacher.priority': 'Priority {n}',
  'teacher.stubStrategyNote':
    "AI was unavailable, so this strategy was built directly from {name}'s learning-gap data.",
  'teacher.recurringMisconception': 'Recurring misconception:',
  'teacher.dismiss': 'Dismiss',
  'teacher.markPlanned': 'Mark as planned',
  'teacher.planned': 'Planned',
  'teacher.dismissed': 'Dismissed',
  'teacher.resolve': 'Resolve',
  'teacher.interventionsLoadError': "Couldn't load suggestions just now.",
  'teacher.noInterventions':
    'No struggling students flagged yet. Generate suggestions from current learning-gap data.',
  'teacher.interventionsGenError':
    "Couldn't generate suggestions just now. Please try again in a moment.",
  'teacher.interventionsFootnote': 'AI strategies guide your follow-up — you stay in control.',

  // Misconception clusters panel
  'teacher.misconceptions': 'Class Misconceptions',
  'teacher.tryInClass': 'Try in class:',
  'teacher.seenTimesOne': 'Seen {count} time · last on {last} · updated {updated}',
  'teacher.seenTimesMany': 'Seen {count} times · last on {last} · updated {updated}',
  'teacher.misconceptionsLoadError': "Couldn't load misconception patterns just now.",
  'teacher.noMisconceptions':
    'No misconception patterns detected yet — they appear once students have a few graded assignments in this class.',
  'teacher.refreshError': "Couldn't refresh just now. Please try again in a moment.",
  'teacher.recomputing': 'Recomputing from recent submissions — new patterns appear here shortly.',
  'teacher.misconceptionsFootnote':
    'Patterns across the whole class — address them once, help everyone.',

  // AI assignment drafts panel
  'teacher.aiDrafts': 'AI Assignment Drafts',
  'teacher.draftPending': "Assembling a draft from your class's weak spots…",
  'teacher.draftPendingNote': 'This usually takes a few seconds.',
  'teacher.draftFailed': "Couldn't put this draft together.",
  'teacher.retrying': 'Retrying…',
  'teacher.tryAgain': 'Try again',
  'teacher.practiceSetDefault': 'Practice set',
  'teacher.assigned': 'Assigned',
  'teacher.viewAssignment': 'View the assignment',
  'teacher.classCanSee': 'your class can see it now.',
  'teacher.stubDraftNote':
    "AI was unavailable, so this draft was built directly from your class's practice data.",
  'teacher.dismissDraftError': "Couldn't dismiss the draft just now. Please try again in a moment.",
  'teacher.approveEllipsis': 'Approve…',
  'teacher.dueDate': 'Due date',
  'teacher.titleLabel': 'Title',
  'teacher.titleOptionalHint': "(optional — keeps the draft's title if blank)",
  'teacher.approveError': "Couldn't approve the draft just now. Please try again in a moment.",
  'teacher.useTryAgainHint': 'Use "Try again" to build a fresh draft.',
  'teacher.assigning': 'Assigning…',
  'teacher.assignToClass': 'Assign to class',
  'teacher.draftsLoadError': "Couldn't load drafts just now.",
  'teacher.noDrafts':
    "No drafts yet — let AI assemble a practice set from this class's weakest chapters, then review and assign it.",
  'teacher.draftStartError': "Couldn't start a draft just now. Please try again in a moment.",
  'teacher.questionsLabel': 'Questions',
  'teacher.difficultyLabel': 'Difficulty',
  'teacher.starting': 'Starting…',
  'teacher.draftAssignment': 'Draft an assignment',
  'teacher.aiProposesFootnote':
    'AI proposes, you decide — nothing reaches students until you approve it.',

  // Question quality panel
  'teacher.questionQuality': 'Question Quality',
  'teacher.flagTooHard': 'Almost no one got this right — check the wording or the keyed answer.',
  'teacher.flagTooEasy': 'Almost everyone got this right — it adds little to the set.',
  'teacher.flagMislabeled': 'Behaves harder or easier than its authored difficulty label.',
  'teacher.flagLowDiscrimination':
    'Stronger students did no better than weaker ones — often a mis-keyed answer.',
  'teacher.flagOk': 'Behaves as authored.',
  'teacher.questionFallback': 'Question #{id}',
  'teacher.correctPct': '{pct} correct',
  'teacher.authoredDifficulty': 'Authored difficulty',
  'teacher.observedDifficulty': 'Observed difficulty',
  'teacher.harderThanLabelled': 'Harder than labelled',
  'teacher.easierThanLabelled': 'Easier than labelled',
  'teacher.discrimination': 'Discrimination',
  'teacher.calibrationSummaryOne': '{flagged} of {total} calibrated question need a look.',
  'teacher.calibrationSummaryMany': '{flagged} of {total} calibrated questions need a look.',
  'teacher.qualityLoadError': "Couldn't load the question analysis just now.",
  'teacher.noFlagged':
    'No questions flagged yet. Calibration needs a handful of student attempts per question — refresh once your class has practised.',
  'teacher.recalibrateStartError':
    "Couldn't start the recalibration just now. Please try again in a moment.",
  'teacher.recalibrating':
    'Recalibrating from recent answers — updated verdicts appear here shortly.',
  'teacher.qualityFootnote':
    'Verdicts come from how your class actually answered — no AI guesswork.',
  'teacher.calibrate': 'Calibrate',

  // Classroom join-code widget
  'teacher.joinCodeHeading': 'Classroom Join Code',
  'teacher.copied': 'Copied!',
  'teacher.copyCode': 'Copy code',
  'teacher.copyLink': 'Copy link',
  'teacher.noExpiry': 'No expiry',
  'teacher.expired': 'Expired',
  'teacher.expiresInUnderHour': 'Expires in <1 hour',
  'teacher.expiresInHours': 'Expires in {hours} hours',
  'teacher.expiresInDays': 'Expires in {days} days',
  'teacher.regenerateWarning':
    "Regenerating invalidates the current code. Students who haven't joined yet will need the new one.",
  'teacher.yesRegenerate': 'Yes, regenerate',
  'teacher.generateJoinCode': 'Generate Join Code',

  // ── Streak badge ─────────────────────────────────────────────────────
  'streak.days': '{count}-day streak',
  'streak.tierStarter': 'On Fire',
  'streak.tierWeek': 'Week Warrior',
  'streak.tierMonth': 'Month Master',
  'streak.tierChampion': 'Champion',
  'streak.best': 'best: {count}',
  'streak.grace': 'grace ✓',
  'streak.graceTitle': 'Grace day used — streak preserved through one missed day',
} as const;

/** Every valid i18n key. Derived from the English dictionary. */
export type LocaleKey = keyof typeof en;

/** Shape every non-English locale must satisfy — full key parity, enforced by tsc. */
export type LocaleDict = Record<LocaleKey, string>;
