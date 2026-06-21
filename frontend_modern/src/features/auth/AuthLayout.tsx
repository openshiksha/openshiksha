import { Link } from 'react-router-dom';
import { ReactNode } from 'react';
import { Logo } from '@/shared/ui';
import { useT, LanguageSwitcher } from '@/shared/i18n';

interface AuthLayoutProps {
  /** Headline rendered above the form panel content. */
  title: string;
  /** Subhead under the title. */
  subtitle?: string;
  /** The form (or any content) for the right-hand paper panel. */
  children: ReactNode;
  /** Optional small footer rendered under the form (e.g. "Sign in" link). */
  footer?: ReactNode;
}

/**
 * Two-column auth shell — chalkboard hero on the left, warm paper form panel
 * on the right. Mirrors `LoginPage`'s layout so login + register all read as
 * one branded flow.
 */
export const AuthLayout = ({ title, subtitle, children, footer }: AuthLayoutProps) => {
  const t = useT();
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel (chalkboard heritage) — hidden on small screens */}
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

      {/* Form panel (paper) */}
      <div className="bg-paper flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-up">
          {/* Compact brand for mobile (brand panel is hidden there) + language toggle */}
          <div className="mb-8 flex items-start justify-between">
            <Link to="/" aria-label="OpenShiksha home" className="inline-block lg:hidden">
              <Logo size="md" />
            </Link>
            <LanguageSwitcher className="ml-auto" />
          </div>

          <h1 className="font-display text-3xl font-semibold text-ink-900">{title}</h1>
          {subtitle && <p className="mt-1 text-ink-500">{subtitle}</p>}

          <div className="mt-8">{children}</div>

          {footer && <div className="mt-8 space-y-2 text-sm text-ink-500">{footer}</div>}
        </div>
      </div>
    </div>
  );
};
