import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { useAuth } from '@/shared/hooks/useAuth';
import { UserRole } from '@/types/index';

interface Tab {
  to: string;
  label: string;
  icon: ReactNode;
  /** Match by prefix so nested routes still highlight the parent tab. */
  matchPrefix?: boolean;
}

const HomeIcon = () => (
  <svg
    aria-hidden
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <path d="M3 11l9-7 9 7" />
    <path d="M5 10v10h14V10" />
  </svg>
);

const BrowseIcon = () => (
  <svg
    aria-hidden
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <path d="M4 5h16M4 12h16M4 19h10" />
  </svg>
);

const PathIcon = () => (
  <svg
    aria-hidden
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <path d="M5 4v6a4 4 0 0 0 4 4h6a4 4 0 0 1 4 4v2" />
    <circle cx="5" cy="4" r="1.6" fill="currentColor" stroke="none" />
    <circle cx="19" cy="20" r="1.6" fill="currentColor" stroke="none" />
  </svg>
);

const QuestionsIcon = () => (
  <svg
    aria-hidden
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <path d="M9 8a3 3 0 1 1 4.5 2.6c-.9.5-1.5 1.1-1.5 2.4" />
    <circle cx="12" cy="17" r="0.9" fill="currentColor" stroke="none" />
  </svg>
);

const PersonIcon = () => (
  <svg
    aria-hidden
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <circle cx="12" cy="8" r="3.4" />
    <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
  </svg>
);

const SchoolIcon = () => (
  <svg
    aria-hidden
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <path d="M3 9l9-4 9 4-9 4-9-4z" />
    <path d="M7 11v4c0 1.7 2.2 3 5 3s5-1.3 5-3v-4" />
  </svg>
);

const tabsFor = (role: UserRole | undefined): Tab[] => {
  switch (role) {
    case UserRole.STUDENT:
    case UserRole.OPEN_STUDENT:
      return [
        { to: '/student', label: 'Home', icon: <HomeIcon /> },
        { to: '/student/browse', label: 'Browse', icon: <BrowseIcon />, matchPrefix: true },
        {
          to: '/student/learning-path',
          label: 'Path',
          icon: <PathIcon />,
          matchPrefix: true,
        },
        { to: '/profile', label: 'Profile', icon: <PersonIcon /> },
      ];
    case UserRole.TEACHER:
      return [
        { to: '/teacher', label: 'Home', icon: <HomeIcon /> },
        {
          to: '/teacher/questions',
          label: 'Questions',
          icon: <QuestionsIcon />,
          matchPrefix: true,
        },
        { to: '/profile', label: 'Profile', icon: <PersonIcon /> },
      ];
    case UserRole.PARENT:
      return [
        { to: '/parent', label: 'Home', icon: <HomeIcon />, matchPrefix: true },
        { to: '/profile', label: 'Profile', icon: <PersonIcon /> },
      ];
    case UserRole.ADMIN:
      return [
        { to: '/admin', label: 'School', icon: <SchoolIcon />, matchPrefix: true },
        { to: '/profile', label: 'Profile', icon: <PersonIcon /> },
      ];
    default:
      return [];
  }
};

const isActive = (pathname: string, tab: Tab): boolean =>
  tab.matchPrefix ? pathname.startsWith(tab.to) : pathname === tab.to;

/**
 * Persistent bottom tab bar on mobile (`<sm`). Sits above the
 * `safe-area-inset-bottom` so it clears the iOS home indicator. Hidden on
 * `sm:` and above where the in-Navbar links take over.
 */
export const BottomNav = () => {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) return null;
  const tabs = tabsFor(user.role);
  if (tabs.length === 0) return null;

  return (
    <nav
      aria-label="Primary"
      className={clsx(
        'fixed inset-x-0 bottom-0 z-30 border-t border-ink-100 bg-white/95 shadow-[0_-10px_30px_rgba(23,32,51,0.08)] backdrop-blur sm:hidden',
        'pb-[env(safe-area-inset-bottom)]',
      )}
    >
      <ul className="mx-auto flex max-w-md items-stretch justify-around px-2 py-1.5">
        {tabs.map((tab) => {
          const active = isActive(location.pathname, tab);
          return (
            <li key={tab.to} className="flex-1">
              <Link
                to={tab.to}
                aria-current={active ? 'page' : undefined}
                className={clsx(
                  'flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-lg px-1.5 py-1 text-[11px] font-semibold leading-tight transition-colors',
                  'focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500',
                  active ? 'text-brand-700' : 'text-ink-500 hover:text-ink-800',
                )}
              >
                <span aria-hidden>{tab.icon}</span>
                <span className="max-w-full truncate">{tab.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
