# OBS-5 — Frontend error reporting, env-gated

## Summary
Wires `@sentry/react` into the existing shared `ErrorBoundary` **only when
`VITE_SENTRY_DSN` is set**. The SDK is loaded via a **dynamic import** behind the
env gate, so when reporting is disabled the entry chunk is unchanged (Vite
constant-folds the guard and Rollup eliminates the import entirely — no Sentry
code ships at all). The friendly localized fallback UI is untouched.

## Classification
New.

## Legacy files referenced
None — observability is greenfield.

## What changed
- **`frontend_modern/package.json`** — added `@sentry/react@^9.47.1`.
- **`frontend_modern/src/vite-env.d.ts`** — typed the optional `VITE_SENTRY_DSN`.
- **`frontend_modern/src/shared/observability/reporter.ts`** (new):
  - `initErrorReporting()` — no-op (no dynamic import) unless `VITE_SENTRY_DSN`
    is set; otherwise dynamically imports `@sentry/react` and inits it
    (`tracesSampleRate: 0`, `sendDefaultPii: false`, env from `VITE_ENV`/`MODE`).
  - `reportError(error, info?)` — no-op unless a DSN is set; otherwise dynamically
    imports the SDK and `captureException`s, attaching the React `componentStack`
    when present. Both swallow errors so reporting can never break the app.
- **`frontend_modern/src/shared/ui/ErrorBoundary.tsx`** — `componentDidCatch` now
  calls `reportError(error, info)` (after the existing `console.error`). Fallback
  UI unchanged.
- **`frontend_modern/src/main.tsx`** — calls `initErrorReporting()` once at app
  root.

## Tests written
- **`reporter.test.ts`** (3 tests) — with no DSN, `initErrorReporting` and
  `reportError` are no-ops that never throw and never import the SDK; `reportError`
  tolerates a null `componentStack`.
- **`ErrorBoundary.test.tsx`** — added a 4th test asserting a caught error is
  forwarded to `reportError` (the existing fallback-render tests still pass).
- All green: `tsc --noEmit`, `eslint` (0 warnings), `vitest run` (7/7 here),
  `npm run build`. **Bundle budget passes** — entry chunk 155.34 kB < 160 kB
  guard; `grep` confirms **no Sentry code in `dist`** when built without a DSN.

## Operational note
Vite inlines `import.meta.env.*` at **build time**. For reporting to be active in
prod, the frontend image must be built with `VITE_SENTRY_DSN` set (CI build env).
Without it the build is byte-for-byte today's. Wiring the DSN into the CI frontend
build is a deploy-config follow-up (no DSN provisioned yet).

## Migration notes
None.

## How to verify
- `npm run type-check && npm run lint && npx vitest run src/shared/observability src/shared/ui/ErrorBoundary.test.tsx`.
- `npm run build && npm run check:budget` → entry chunk under 160 kB; no Sentry
  chunk emitted when `VITE_SENTRY_DSN` is unset.

## Next steps
Batch 1 (OBS-1..5) complete. Batch 2 — metrics & dashboards (`/metrics` + Grafana
starter).
