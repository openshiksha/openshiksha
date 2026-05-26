import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { UserRole } from '@/types/index';

const ROLE_LABELS: Record<string, string> = {
  [UserRole.STUDENT]: 'Student',
  [UserRole.TEACHER]: 'Teacher',
  [UserRole.PARENT]: 'Parent',
  [UserRole.ADMIN]: 'Admin',
  [UserRole.OPEN_STUDENT]: 'Student',
};

const ROLE_COLORS: Record<string, string> = {
  [UserRole.STUDENT]: 'bg-blue-100 text-blue-700',
  [UserRole.TEACHER]: 'bg-green-100 text-green-700',
  [UserRole.PARENT]: 'bg-purple-100 text-purple-700',
  [UserRole.ADMIN]: 'bg-red-100 text-red-700',
  [UserRole.OPEN_STUDENT]: 'bg-blue-100 text-blue-700',
};

export const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close mobile menu on route change
  useEffect(() => {
    setMenuOpen(false);
    setUserMenuOpen(false);
  }, [location.pathname]);

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

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Brand + Desktop nav links */}
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs font-bold">OS</span>
              </div>
              <span className="font-semibold text-gray-900 hidden sm:block">OpenShiksha</span>
            </Link>

            {/* Desktop nav — hidden on mobile */}
            <div className="hidden sm:flex items-center gap-1">
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
            </div>
          </div>

          {/* Right: User avatar dropdown (desktop) + hamburger (mobile) */}
          <div className="flex items-center gap-2">
            {user && (
              <div className="relative hidden sm:block" ref={userMenuRef}>
                <button
                  onClick={() => setUserMenuOpen((v) => !v)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="w-7 h-7 bg-indigo-100 rounded-full flex items-center justify-center">
                    <span className="text-indigo-700 text-xs font-bold">
                      {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm text-gray-700">{user.first_name || user.username}</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      active
        ? 'bg-indigo-50 text-indigo-700'
        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
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
