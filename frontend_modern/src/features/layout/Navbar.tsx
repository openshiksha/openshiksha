import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { Logo } from '@/shared/ui';
import { LanguageSwitcher } from '@/shared/i18n';
import { UserRole } from '@/types/index';

const ROLE_LABELS: Record<string, string> = {
  [UserRole.STUDENT]: 'Student',
  [UserRole.TEACHER]: 'Teacher',
  [UserRole.PARENT]: 'Parent',
  [UserRole.ADMIN]: 'Admin',
  [UserRole.OPEN_STUDENT]: 'Student',
};

const ROLE_COLORS: Record<string, string> = {
  [UserRole.STUDENT]: 'bg-brand-100 text-brand-800',
  [UserRole.TEACHER]: 'bg-emerald-100 text-emerald-800',
  [UserRole.PARENT]: 'bg-amber-100 text-amber-800',
  [UserRole.ADMIN]: 'bg-rose-100 text-rose-800',
  [UserRole.OPEN_STUDENT]: 'bg-brand-100 text-brand-800',
};

export const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const hamburgerRef = useRef<HTMLButtonElement>(null);

  // Close menus on route change (adjust state during render — react.dev/learn/you-might-not-need-an-effect)
  const [prevPathname, setPrevPathname] = useState(location.pathname);
  if (location.pathname !== prevPathname) {
    setPrevPathname(location.pathname);
    setMenuOpen(false);
    setUserMenuOpen(false);
  }

  // Close dropdowns on outside click + ESC
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (userMenuOpen) setUserMenuOpen(false);
        if (menuOpen) {
          setMenuOpen(false);
          hamburgerRef.current?.focus();
        }
      }
    };
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [menuOpen, userMenuOpen]);

  const isStudent = user?.role === UserRole.STUDENT || user?.role === UserRole.OPEN_STUDENT;
  const isTeacher = user?.role === UserRole.TEACHER;
  const isParent = user?.role === UserRole.PARENT;
  const isAdmin = user?.role === UserRole.ADMIN;

  return (
    <nav
      aria-label="Top"
      className="bg-white/90 backdrop-blur border-b border-ink-100 sticky top-0 z-20 pt-[env(safe-area-inset-top)]"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Brand + Desktop nav links */}
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className="flex items-center rounded focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
              aria-label="OpenShiksha home"
            >
              <Logo size="sm" className="hidden sm:inline-flex" />
              <Logo size="sm" variant="mark" className="sm:hidden" />
            </Link>

            {/* Desktop nav — hidden on mobile */}
            <div className="hidden sm:flex items-center gap-5">
              {isStudent && (
                <>
                  <NavLink to="/student" active={location.pathname === '/student'}>
                    Dashboard
                  </NavLink>
                  <NavLink
                    to="/student/browse"
                    active={location.pathname.startsWith('/student/browse')}
                  >
                    Browse
                  </NavLink>
                  <NavLink
                    to="/student/learning-path"
                    active={location.pathname.startsWith('/student/learning-path')}
                  >
                    Learning Path
                  </NavLink>
                </>
              )}
              {isTeacher && (
                <>
                  <NavLink to="/teacher" active={location.pathname === '/teacher'}>
                    Dashboard
                  </NavLink>
                  <NavLink
                    to="/teacher/questions"
                    active={location.pathname.startsWith('/teacher/questions')}
                  >
                    Questions
                  </NavLink>
                </>
              )}
              {isParent && (
                <NavLink to="/parent" active={location.pathname.startsWith('/parent')}>
                  Dashboard
                </NavLink>
              )}
              {isAdmin && (
                <NavLink to="/admin" active={location.pathname.startsWith('/admin')}>
                  School Admin
                </NavLink>
              )}
            </div>
          </div>

          {/* Right: Language toggle + user avatar dropdown (desktop) + hamburger (mobile) */}
          <div className="flex items-center gap-2">
            <LanguageSwitcher className="hidden sm:inline-flex" />
            {user && (
              <div className="relative hidden sm:block" ref={userMenuRef}>
                <button
                  onClick={() => setUserMenuOpen((v) => !v)}
                  aria-haspopup="menu"
                  aria-expanded={userMenuOpen}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-ink-50 transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
                >
                  <div className="w-7 h-7 bg-brand-100 rounded-full flex items-center justify-center">
                    <span className="text-brand-700 text-xs font-bold">
                      {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm text-ink-700">{user.first_name || user.username}</span>
                  <svg
                    aria-hidden
                    className="w-4 h-4 text-ink-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {userMenuOpen && (
                  <div
                    role="menu"
                    className="absolute right-0 mt-1 w-44 bg-white border border-ink-100 rounded-lg shadow-card z-30 py-1"
                  >
                    <Link
                      to="/profile"
                      role="menuitem"
                      className="block px-4 py-2 text-sm text-ink-700 hover:bg-ink-50 transition-colors focus-visible:outline-hidden focus-visible:bg-ink-50"
                    >
                      Profile
                    </Link>
                    {isStudent && (
                      <Link
                        to="/student/proficiency"
                        role="menuitem"
                        className="block px-4 py-2 text-sm text-ink-700 hover:bg-ink-50 transition-colors focus-visible:outline-hidden focus-visible:bg-ink-50"
                      >
                        My Progress
                      </Link>
                    )}
                    <div className="border-t border-ink-100 my-1" />
                    <button
                      onClick={logout}
                      role="menuitem"
                      className="w-full text-left px-4 py-2 text-sm text-rose-700 hover:bg-rose-50 transition-colors focus-visible:outline-hidden focus-visible:bg-rose-50"
                    >
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Hamburger button — mobile only. Bottom-tab bar covers primary nav,
                so this sheet now only hosts account actions + role-specific
                secondary links (e.g. student Proficiency). */}
            {user && (
              <button
                ref={hamburgerRef}
                className="sm:hidden p-2 rounded-md text-ink-500 hover:text-ink-800 hover:bg-ink-100 transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
                onClick={() => setMenuOpen((v) => !v)}
                aria-label={menuOpen ? 'Close account menu' : 'Open account menu'}
                aria-expanded={menuOpen}
                aria-controls="navbar-mobile-sheet"
              >
                {menuOpen ? (
                  <svg
                    aria-hidden
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                ) : (
                  <svg
                    aria-hidden
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </svg>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile account sheet */}
      {menuOpen && user && (
        <div
          id="navbar-mobile-sheet"
          className="sm:hidden border-t border-ink-100 bg-white z-20"
        >
          <div className="px-4 py-3 space-y-1">
            {/* User identity */}
            <div className="flex items-center gap-2 pb-3 border-b border-ink-100 mb-2">
              <div className="w-8 h-8 bg-brand-100 rounded-full flex items-center justify-center">
                <span className="text-brand-700 text-xs font-bold">
                  {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
                </span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-ink-900 truncate">
                  {user.first_name || user.username}
                </p>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${
                    ROLE_COLORS[user.role] ?? 'bg-ink-100 text-ink-700'
                  }`}
                >
                  {ROLE_LABELS[user.role] ?? user.role}
                </span>
              </div>
            </div>

            <p className="px-3 pt-1 text-[10px] font-semibold uppercase tracking-widest text-ink-400">
              Account
            </p>
            <MobileNavLink to="/profile">Profile</MobileNavLink>
            {isStudent && <MobileNavLink to="/student/proficiency">My Progress</MobileNavLink>}
            <div className="px-3 py-2">
              <LanguageSwitcher />
            </div>

            <div className="pt-2 border-t border-ink-100 mt-2">
              <button
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="w-full text-left px-3 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-50 rounded-md transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

interface NavLinkProps {
  to: string;
  active: boolean;
  children: React.ReactNode;
}

const NavLink = ({ to, active, children }: NavLinkProps) => (
  <Link
    to={to}
    aria-current={active ? 'page' : undefined}
    className={`px-1 py-2 text-sm font-medium rounded transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
      active ? 'chalk-underline text-ink-900' : 'text-ink-500 hover:text-ink-900'
    }`}
  >
    {children}
  </Link>
);

const MobileNavLink = ({ to, children }: { to: string; children: React.ReactNode }) => (
  <Link
    to={to}
    className="block px-3 py-2.5 text-sm font-medium text-ink-700 hover:bg-ink-100 rounded-md transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
  >
    {children}
  </Link>
);
