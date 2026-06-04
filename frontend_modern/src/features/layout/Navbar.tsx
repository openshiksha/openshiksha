import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { Logo } from '@/shared/ui';
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

  // Close menus on route change (adjust state during render — react.dev/learn/you-might-not-need-an-effect)
  const [prevPathname, setPrevPathname] = useState(location.pathname);
  if (location.pathname !== prevPathname) {
    setPrevPathname(location.pathname);
    setMenuOpen(false);
    setUserMenuOpen(false);
  }

  // Close user dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const isStudent = user?.role === UserRole.STUDENT || user?.role === UserRole.OPEN_STUDENT;
  const isTeacher = user?.role === UserRole.TEACHER;
  const isParent = user?.role === UserRole.PARENT;
  const isAdmin = user?.role === UserRole.ADMIN;

  return (
    <nav className="bg-white/90 backdrop-blur border-b border-ink-100 sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Brand + Desktop nav links */}
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center" aria-label="OpenShiksha home">
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

          {/* Right: User avatar dropdown (desktop) + hamburger (mobile) */}
          <div className="flex items-center gap-2">
            {user && (
              <div className="relative hidden sm:block" ref={userMenuRef}>
                <button
                  onClick={() => setUserMenuOpen((v) => !v)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-ink-50 transition-colors"
                >
                  <div className="w-7 h-7 bg-brand-100 rounded-full flex items-center justify-center">
                    <span className="text-brand-700 text-xs font-bold">
                      {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm text-ink-700">{user.first_name || user.username}</span>
                  <svg className="w-4 h-4 text-ink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-1 w-44 bg-white border border-gray-200 rounded-lg shadow-lg z-30 py-1">
                    <Link
                      to="/profile"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      Profile
                    </Link>
                    <div className="border-t border-gray-100 my-1" />
                    <button
                      onClick={logout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Hamburger button — mobile only */}
            {user && (
              <button
                className="sm:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
                onClick={() => setMenuOpen((v) => !v)}
                aria-label="Toggle navigation"
                aria-expanded={menuOpen}
              >
                {menuOpen ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && user && (
        <div className="sm:hidden border-t border-gray-200 bg-white z-20">
          <div className="px-4 py-3 space-y-1">
            {/* User identity */}
            <div className="flex items-center gap-2 pb-3 border-b border-gray-100 mb-2">
              <span className="text-sm font-medium text-gray-900">
                {user.first_name || user.username}
              </span>
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                  ROLE_COLORS[user.role] ?? 'bg-gray-100 text-gray-700'
                }`}
              >
                {ROLE_LABELS[user.role] ?? user.role}
              </span>
            </div>

            {/* Role-specific nav links */}
            {isStudent && (
              <>
                <MobileNavLink to="/student">Dashboard</MobileNavLink>
                <MobileNavLink to="/student/browse">Browse Subjects</MobileNavLink>
                <MobileNavLink to="/student/learning-path">Learning Path</MobileNavLink>
                <MobileNavLink to="/student/proficiency">My Progress</MobileNavLink>
              </>
            )}
            {isTeacher && (
              <>
                <MobileNavLink to="/teacher">Dashboard</MobileNavLink>
                <MobileNavLink to="/teacher/questions">Questions</MobileNavLink>
              </>
            )}
            {isParent && <MobileNavLink to="/parent">Dashboard</MobileNavLink>}
            {isAdmin && <MobileNavLink to="/admin">School Admin</MobileNavLink>}

            {/* Profile + Sign out */}
            <div className="pt-2 border-t border-gray-100 mt-2 space-y-1">
              <MobileNavLink to="/profile">Profile</MobileNavLink>
              <button
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="w-full text-left px-3 py-2.5 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
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
    className={`px-1 py-2 text-sm font-medium transition-colors ${
      active
        ? 'chalk-underline text-ink-900'
        : 'text-ink-500 hover:text-ink-900'
    }`}
  >
    {children}
  </Link>
);

const MobileNavLink = ({ to, children }: { to: string; children: React.ReactNode }) => (
  <Link
    to={to}
    className="block px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
  >
    {children}
  </Link>
);
