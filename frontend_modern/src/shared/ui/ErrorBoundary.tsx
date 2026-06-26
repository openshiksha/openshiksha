import { Component, ErrorInfo, ReactNode } from 'react';
import { reportError } from '../observability/reporter';

interface Props {
  children: ReactNode;
  /** Optional custom fallback. Receives the error + a reset handler. */
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * V2 error boundary. Catches render-time errors in its subtree and shows a
 * warm-paper recovery card with a "Try again" action. Must be a class component
 * — hooks can't catch errors.
 *
 * Wrap the authenticated content outlet, NOT the router or auth gate, so that
 * navigation/redirects aren't swallowed.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    if (typeof console !== 'undefined') {
      console.error('[ErrorBoundary]', error, info.componentStack);
    }
    // OBS-5 — report to Sentry when VITE_SENTRY_DSN is set; no-op otherwise.
    reportError(error, info);
  }

  reset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }
      return (
        <div className="bg-paper flex min-h-[60vh] items-center justify-center px-6 py-12">
          <div className="os-card max-w-md p-8 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-100">
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                width="28"
                height="28"
                fill="none"
                className="text-rose-600"
              >
                <path
                  d="M12 8v5m0 3h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 4.99c-.77-1.33-2.69-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h2 className="font-display text-xl font-semibold text-ink-900">
              Something went wrong
            </h2>
            <p className="mt-2 text-sm text-ink-500">
              The page hit an unexpected error. Try again — if it keeps happening,
              reload the app or sign in again.
            </p>
            <button
              type="button"
              onClick={this.reset}
              className="btn-brand mt-6"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
