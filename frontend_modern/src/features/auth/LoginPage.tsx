import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { Logo, Button } from '@/shared/ui';
import { useT, LanguageSwitcher } from '@/shared/i18n';
import { useLoginMutation } from './useLoginMutation';

export const LoginPage = () => {
  const { isAuthenticated, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const t = useT();

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
            {t('auth.heroHeadline')}
          </h2>
          <p className="mt-4 text-ink-200">{t('auth.heroSubtext')}</p>
        </div>
        <p className="text-sm text-ink-300">{t('auth.heroFootnote')}</p>
      </div>

      {/* ── Form panel (paper) ─────────────────────────────────────────── */}
      <div className="bg-paper flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-up">
          {/* Compact brand for mobile (brand panel is hidden) + language toggle */}
          <div className="mb-8 flex items-start justify-between">
            <Link
              to="/"
              aria-label="OpenShiksha home"
              className="inline-block lg:hidden"
            >
              <Logo size="md" />
            </Link>
            <LanguageSwitcher className="ml-auto" />
          </div>

          <h1 className="font-display text-3xl font-semibold text-ink-900">
            {t('login.title')}
          </h1>
          <p className="mt-1 text-ink-500">{t('login.subtitle')}</p>

          <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-5">
            <div>
              <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-ink-700">
                {t('login.username')}
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-brand"
                placeholder={t('login.usernamePlaceholder')}
                disabled={loginMutation.isPending}
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-ink-700">
                {t('login.password')}
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-brand"
                placeholder={t('login.passwordPlaceholder')}
                disabled={loginMutation.isPending}
              />
            </div>

            {loginMutation.isError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">
                {t('login.error')}
              </div>
            )}

            <Button
              type="submit"
              size="lg"
              disabled={loginMutation.isPending || !username || !password}
              className="w-full"
            >
              {loginMutation.isPending ? t('login.submitting') : t('login.submit')}
            </Button>
          </form>

          <div className="mt-8 space-y-2 text-sm text-ink-500">
            <p>
              {t('login.noAccount')}{' '}
              <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-800">
                {t('login.registerLink')}
              </Link>
            </p>
            <p>
              {t('login.schoolQuestion')}{' '}
              <Link to="/enquire" className="font-semibold text-brand-700 hover:text-brand-800">
                {t('login.enquireLink')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
