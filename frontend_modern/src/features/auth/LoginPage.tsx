import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { Logo, Button } from '@/shared/ui';
import { useLoginMutation } from './useLoginMutation';

export const LoginPage = () => {
  const { isAuthenticated, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useLoginMutation();

  // Already logged in — let the role-aware home route redirect onward.
  if (isAuthenticated && user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ username, password });
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* ── Brand panel (chalkboard heritage) ──────────────────────────── */}
      <div className="bg-chalkboard relative hidden flex-col justify-between overflow-hidden p-12 lg:flex">
        <Link to="/" aria-label="OpenShiksha home" className="w-fit">
          <Logo size="md" wordmarkClassName="text-white" />
        </Link>
        <div className="max-w-md">
          <h2 className="font-display text-4xl font-semibold leading-tight text-white text-balance">
            Unlock learning, one question at a time.
          </h2>
          <p className="mt-4 text-ink-200">
            Adaptive practice, instant correction, and analytics that show every
            student exactly what to learn next.
          </p>
        </div>
        <p className="text-sm text-ink-300">CBSE · Classes 7–10 · English &amp; हिन्दी</p>
      </div>

      {/* ── Form panel (paper) ─────────────────────────────────────────── */}
      <div className="bg-paper flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-up">
          {/* Compact brand for mobile (brand panel is hidden) */}
          <div className="mb-8 lg:hidden">
            <Link to="/" aria-label="OpenShiksha home" className="inline-block">
              <Logo size="md" />
            </Link>
          </div>

          <h1 className="font-display text-3xl font-semibold text-ink-900">Welcome back</h1>
          <p className="mt-1 text-ink-500">Sign in to continue learning.</p>

          <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-5">
            <div>
              <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-ink-700">
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-brand"
                placeholder="Enter your username"
                disabled={loginMutation.isPending}
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-ink-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-brand"
                placeholder="Enter your password"
                disabled={loginMutation.isPending}
              />
            </div>

            {loginMutation.isError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
                Invalid username or password. Please try again.
              </div>
            )}

            <Button
              type="submit"
              size="lg"
              disabled={loginMutation.isPending || !username || !password}
              className="w-full"
            >
              {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          <div className="mt-8 space-y-2 text-sm text-ink-500">
            <p>
              Don&apos;t have an account?{' '}
              <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-800">
                Register
              </Link>
            </p>
            <p>
              Are you a school?{' '}
              <Link to="/enquire" className="font-semibold text-brand-700 hover:text-brand-800">
                Enquire about OpenShiksha
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
