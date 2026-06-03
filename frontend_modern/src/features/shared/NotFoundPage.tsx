import { Link } from 'react-router-dom';
import { Logo } from '@/shared/ui';

/**
 * Branded 404 page. Warm paper, keyhole mark, calm copy, "Back home" CTA. The
 * catch-all `*` route in `App.tsx` renders this.
 */
export const NotFoundPage = () => (
  <div className="bg-paper flex min-h-screen flex-col items-center justify-center px-6 py-12 text-center">
    <Logo size="lg" float />
    <p className="mt-8 font-display text-6xl font-semibold text-brand-600 sm:text-7xl">404</p>
    <h1 className="mt-4 font-display text-2xl font-semibold text-ink-900 sm:text-3xl">
      Nothing behind this door
    </h1>
    <p className="mt-3 max-w-md text-ink-500">
      The page you were looking for has moved or never existed. Let&apos;s get
      you back to learning.
    </p>
    <Link to="/" className="btn-brand mt-8">
      Back to home
    </Link>
  </div>
);
