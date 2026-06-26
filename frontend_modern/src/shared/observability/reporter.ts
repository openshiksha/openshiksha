import type { ErrorInfo } from 'react';

/**
 * Frontend error reporting (OBS-5), env-gated on `VITE_SENTRY_DSN`.
 *
 * `@sentry/react` is **dynamically imported** only when a DSN is configured, so
 * the entry chunk is byte-for-byte unchanged when reporting is disabled (the perf
 * budget — see `scripts/check-bundle-budget.mjs` — is defended). With no DSN both
 * functions are no-ops and the SDK is never loaded.
 */

let initialized = false;

function dsn(): string | undefined {
  const value = import.meta.env.VITE_SENTRY_DSN;
  return value && value.length > 0 ? value : undefined;
}

/** Initialise Sentry once. No-op (and no dynamic import) unless a DSN is set. */
export function initErrorReporting(): void {
  if (initialized || !dsn()) return;
  initialized = true;
  void import('@sentry/react')
    .then((Sentry) => {
      Sentry.init({
        dsn: dsn(),
        environment: import.meta.env.VITE_ENV || import.meta.env.MODE,
        tracesSampleRate: 0,
        sendDefaultPii: false,
      });
    })
    .catch(() => {
      // Observability wiring must never break the app — allow a later retry.
      initialized = false;
    });
}

/**
 * Report a caught React render error. No-op (no dynamic import) unless a DSN is
 * set, so the disabled path stays free of the SDK.
 */
export function reportError(error: Error, info?: ErrorInfo): void {
  if (!dsn()) return;
  const componentStack = info?.componentStack ?? undefined;
  void import('@sentry/react')
    .then((Sentry) => {
      Sentry.captureException(error, {
        contexts: componentStack ? { react: { componentStack } } : undefined,
      });
    })
    .catch(() => {
      /* swallow — reporting must never throw */
    });
}
