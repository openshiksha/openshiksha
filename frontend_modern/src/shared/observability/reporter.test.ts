import { describe, expect, it, vi, afterEach } from 'vitest';
import { initErrorReporting, reportError } from './reporter';

// With no VITE_SENTRY_DSN configured (the default in the test env), both
// functions must early-return without ever importing the SDK.

describe('error reporter (no DSN)', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('initErrorReporting is a no-op when DSN unset', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    // Must not throw and must not attempt any dynamic import.
    expect(() => initErrorReporting()).not.toThrow();
  });

  it('reportError is a no-op when DSN unset', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    expect(() => reportError(new Error('boom'))).not.toThrow();
  });

  it('reportError tolerates missing componentStack', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    expect(() => reportError(new Error('boom'), { componentStack: null })).not.toThrow();
  });
});
