import { Link } from 'react-router-dom';
import { AuthLayout } from './AuthLayout';

export const RegisterPage = () => (
  <AuthLayout
    title="Create your account"
    subtitle="How would you like to learn?"
    footer={
      <p>
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
          Sign in
        </Link>
      </p>
    }
  >
    <div className="space-y-4">
      <Link
        to="/register/school"
        className="os-card group flex items-start gap-4 p-5 transition-shadow hover:shadow-lift focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 transition-colors group-hover:bg-brand-100">
          <svg className="h-6 w-6 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <div className="min-w-0">
          <h2 className="font-display text-lg font-semibold text-ink-900 group-hover:text-brand-700">
            Join a school
          </h2>
          <p className="mt-1 text-sm text-ink-500">
            Use a classroom join code from your teacher to enroll automatically.
          </p>
        </div>
      </Link>

      <Link
        to="/register/open"
        className="os-card group flex items-start gap-4 p-5 transition-shadow hover:shadow-lift focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-50 transition-colors group-hover:bg-emerald-100">
          <svg className="h-6 w-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
        </div>
        <div className="min-w-0">
          <h2 className="font-display text-lg font-semibold text-ink-900 group-hover:text-emerald-700">
            Study independently
          </h2>
          <p className="mt-1 text-sm text-ink-500">
            Practice from the shared question bank at your own pace — no school needed.
          </p>
        </div>
      </Link>
    </div>
  </AuthLayout>
);
