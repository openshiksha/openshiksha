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
