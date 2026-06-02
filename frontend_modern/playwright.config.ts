import { defineConfig, devices } from '@playwright/test';

// Playwright config for OpenShiksha frontend_modern.
//
// Scope (2026-06-01): purely client-side smoke tests against public routes
// (e.g. /design). Tests must NOT depend on the Django backend — the CI job
// only boots the Vite preview server, not the full Docker stack.
//
// When we add tests that need the backend, run them in a separate project
// here and gate the matching CI job on a Docker compose stack.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    // `vite preview` serves the production build on :4173. Using the built
    // output (not `vite dev`) keeps the smoke test close to what users see.
    command: 'npm run build && npm run preview -- --port 4173 --strictPort',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
