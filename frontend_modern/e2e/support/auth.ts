import type { Page, Route } from '@playwright/test';

// ────────────────────────────────────────────────────────────────────────────
// Authenticated Playwright harness for the per-route axe audit (A11Y-6).
//
// The `frontend-e2e` CI job runs `vite preview` with **no backend**, so the
// authenticated student routes can't log in for real. Instead we:
//   1. seed the JWT keys the app's auth layer reads from localStorage
//      (`access_token` / `refresh_token` — see src/api/client.ts +
//      src/api/auth.ts), so `ProtectedRoute` admits a student; and
//   2. intercept every `**/api/v1/**` request with `page.route` and fulfil the
//      core-loop reads with tiny static fixtures — axe only needs the DOM to
//      render, not real data.
//
// Reusable for the teacher/parent surfaces in a later batch: add their reads to
// `routeHandler` and a role to `STUDENT_USER`.
// ────────────────────────────────────────────────────────────────────────────

/** A minimal student `User` matching src/types/index.ts `User`. */
export const STUDENT_USER = {
  id: 1,
  username: 'a11y_student',
  email: 'student@example.com',
  first_name: 'Asha',
  last_name: 'Student',
  role: 'student',
  grade: 8,
  preferred_language: 'en',
};

/** A minimal teacher `User` (A11Y-9 — teacher core surfaces). */
export const TEACHER_USER = {
  id: 2,
  username: 'a11y_teacher',
  email: 'teacher@example.com',
  first_name: 'Meera',
  last_name: 'Teacher',
  role: 'teacher',
  grade: null,
  preferred_language: 'en',
};

/** A minimal parent `User` with one child (A11Y-9 — parent core surfaces). */
export const PARENT_USER = {
  id: 3,
  username: 'a11y_parent',
  email: 'parent@example.com',
  first_name: 'Sunil',
  last_name: 'Parent',
  role: 'parent',
  grade: null,
  preferred_language: 'en',
};

/** The child the parent surfaces resolve via `/users/me/children/`. */
const CHILD_USER = {
  ...STUDENT_USER,
  id: 10,
  username: 'a11y_child',
  first_name: 'Ravi',
};

const paginated = (results: unknown[]) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
});

const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });

// ── Core-loop fixtures ───────────────────────────────────────────────────────

const SUBPARTS = [
  {
    id: 11,
    index: 0,
    subpart_type: 'mcq',
    tags: [],
    question_text: 'What is 2 + 2?',
    options: [
      { key: 'A', text: 'Three' },
      { key: 'B', text: 'Four' },
      { key: 'C', text: 'Five' },
      { key: 'D', text: 'Six' },
    ],
  },
  {
    id: 12,
    index: 1,
    // A numeric (and the fill-blank fallback) renders a bare <input> whose only
    // accessible name today is its placeholder — the labelling gap A11Y-7 fixes.
    subpart_type: 'numeric',
    tags: [],
    question_text: 'Enter the value of 5 × 3.',
    options: null,
  },
];

const QUESTION = {
  id: 1,
  standard: 8,
  subject: 1,
  chapter: 1,
  question_type: 'mcq',
  difficulty: 2,
  tags: [],
  subparts: SUBPARTS,
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const PROBLEM_SET = {
  id: 1,
  title: 'Arithmetic Warm-up',
  description: 'A short practice set.',
  chapter: { id: 1, name: 'Whole Numbers' },
  subject: { id: 1, name: 'Mathematics' },
  standard: { id: 8, name: 'Standard 8' },
  question_count: 1,
  estimated_minutes: 10,
  is_active: true,
  is_remedial: false,
  source_assignment: null,
};

const ASSIGNMENT_DETAIL = {
  id: 1,
  subject_room: 1,
  subject_room_display: 'Mathematics · 8A',
  problem_set: { ...PROBLEM_SET, questions: [QUESTION] },
  assigned_by: 2,
  assigned_at: '2026-06-01T00:00:00Z',
  due_at: '2026-12-31T00:00:00Z',
  number: 1,
  average_score: null,
  completion_rate: null,
  submission_count: 0,
  student_count: 20,
  status: 'active',
};

const ASSIGNMENT_SUMMARY = { ...ASSIGNMENT_DETAIL, problem_set: PROBLEM_SET };

// A non-submitted submission so AssignmentDetailPage skips the create-POST and
// renders the answer form (not the post-submit score card).
const SUBMISSION = {
  id: 1,
  assignment: 1,
  student: 1,
  score: null,
  completion: 0,
  answers: {},
  submitted_at: null,
  is_revised: false,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-01T00:00:00Z',
};

const SRS_DRILL = {
  entry_id: 1,
  chapter_name: 'Whole Numbers',
  subject_name: 'Mathematics',
  questions: [QUESTION],
};

const STREAK = {
  current_streak: 3,
  longest_streak: 7,
  last_activity_date: '2026-06-20',
  streak_grace_used: false,
  milestone_tier: 'week',
};

// ── Dispatch ─────────────────────────────────────────────────────────────────

/** The signed-in user shape the dispatch resolves `/users/me/` to. */
type SessionUser = typeof STUDENT_USER | typeof TEACHER_USER | typeof PARENT_USER;

// The dispatch is parametrized by the session user so the same fixtures serve
// the student, teacher, and parent core surfaces (A11Y-6 → A11Y-9). Only the
// identity reads (`/users/me/`, `/users/me/children/`) vary by role; the list
// reads are role-agnostic (the backend scopes them by the JWT, which we stub).
function makeRouteHandler(user: SessionUser) {
  return function routeHandler(route: Route): Promise<void> {
    const url = new URL(route.request().url());
    const p = url.pathname;

    // Auth gate + identity.
    if (p.endsWith('/auth/verify/')) return json(route, {});
    if (p.endsWith('/auth/refresh/')) return json(route, { access: 'fake-access' });
    if (p.endsWith('/users/me/children/')) return json(route, [CHILD_USER]);
    if (p.endsWith('/users/me/')) return json(route, user);
    if (p.endsWith('/users/me/streak/')) return json(route, STREAK);

    // Object (non-list) endpoints that signal "nothing yet" with a 404 — their
    // hooks map 404 → null/disabled and render an empty state, whereas a
    // paginated-empty body would be the wrong shape and throw in a consumer.
    if (p.endsWith('/ai/practice-plans/today/')) return json(route, { detail: 'No plan' }, 404);
    if (p.endsWith('/push/vapid-public-key/')) return json(route, { detail: 'Disabled' }, 404);

    // Core-loop reads (shared across roles).
    if (/\/assignments\/\d+\/$/.test(p)) return json(route, ASSIGNMENT_DETAIL);
    if (p.endsWith('/assignments/')) return json(route, paginated([ASSIGNMENT_SUMMARY]));
    if (p.endsWith('/submissions/')) return json(route, paginated([SUBMISSION]));
    if (p.endsWith('/proficiency/')) return json(route, paginated([]));
    if (/\/spaced-repetition\/\d+\/review\/$/.test(p)) return json(route, SRS_DRILL);

    // Everything else: an empty paginated page is a safe default for the list
    // reads (videos, announcements, recommendations, learning-paths, srs/due,
    // subject-rooms, problem-sets, questions…) — each renders its branded empty
    // state, which still carries the page heading and landmarks axe needs.
    return json(route, paginated([]));
  };
}

async function setupAuth(page: Page, user: SessionUser): Promise<void> {
  await page.addInitScript(() => {
    try {
      localStorage.setItem('access_token', 'fake-access-token');
      localStorage.setItem('refresh_token', 'fake-refresh-token');
    } catch {
      /* localStorage unavailable — nothing to seed */
    }
  });
  await page.route('**/api/v1/**', makeRouteHandler(user));
}

/** Seed a student session + stub the core-loop API. Call before `page.goto`. */
export const setupStudentAuth = (page: Page): Promise<void> => setupAuth(page, STUDENT_USER);

/** Seed a teacher session + stub the teacher reads. Call before `page.goto`. */
export const setupTeacherAuth = (page: Page): Promise<void> => setupAuth(page, TEACHER_USER);

/** Seed a parent session (one child) + stub the parent reads. */
export const setupParentAuth = (page: Page): Promise<void> => setupAuth(page, PARENT_USER);

/** Role → setup helper, for the parameterized a11y route table. */
export const AUTH_SETUP: Record<'student' | 'teacher' | 'parent', (page: Page) => Promise<void>> = {
  student: setupStudentAuth,
  teacher: setupTeacherAuth,
  parent: setupParentAuth,
};
