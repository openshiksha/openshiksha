import { test, expect } from '@playwright/test';
import { AUTH_SETUP } from './support/auth';

// Regression guard for the auth-bootstrap deep-link bounce.
//
// Symptom: a hard navigation / deep-link to a ProtectedRoute (e.g.
// /teacher/questions) rendered the role *dashboard* at /teacher instead of the
// requested page.
//
// Root cause: while `PersistQueryClientProvider` rehydrates the query cache from
// IndexedDB (MSO-4), queries are held idle — `status: 'pending'` but
// `fetchStatus: 'idle'`. React Query's `isLoading` (= isPending && isFetching)
// is therefore *false* during that restore window even though the auth-verify
// result is still unknown. `useAuth` used to gate on `isLoading`, so the app
// painted an unauthenticated tree for the first frame; `ProtectedRoute` saw
// `isAuthenticated === false` and redirected to /login. Moments later verify
// resolved `true`, and `LoginPage` (now mounted at /login) bounced the verified
// user to their role home (`/` → defaultPath) — silently dropping the deep
// link. The fix gates `useAuth` on `isPending` + `useIsRestoring()` instead.
//
// This reproduces in both `vite dev` and `vite preview` (it is the restore race,
// not the service worker). The runner here is `vite preview` (no backend), so we
// seed a JWT + stub the API exactly as the a11y audit does.

test.describe('protected deep-links survive auth bootstrap', () => {
  test('hard nav to /teacher/questions renders the Question Bank, not the dashboard', async ({
    page,
  }) => {
    await AUTH_SETUP.teacher(page);

    await page.goto('/teacher/questions');
    await page.waitForLoadState('networkidle');

    // The URL must not have been rewritten to the teacher dashboard.
    expect(new URL(page.url()).pathname).toBe('/teacher/questions');

    // …and the rendered page must be the Question Bank heading, not
    // "Teacher dashboard".
    const h1 = page.locator('h1').first();
    await expect(h1).toBeVisible();
    await expect(h1).toHaveText('Question Bank');
  });
});
