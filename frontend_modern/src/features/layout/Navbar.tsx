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

  const isStudent = user?.role === UserRole.STUDENT || user?.role === UserRole.OPEN_STUDENT;
  const isTeacher = user?.role === UserRole.TEACHER;
  const isParent = user?.role === UserRole.PARENT;

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Brand + Nav links */}
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs font-bold">OS</span>
              </div>
              <span className="font-semibold text-gray-900 hidden sm:block">OpenShiksha</span>
            </Link>

            <div className="flex items-center gap-1">
              {isStudent && (
                <>
                  <NavLink to="/student" active={location.pathname === '/student'}>
                    Dashboard
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

          {/* Right: User info + logout */}
          {user && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-700 hidden sm:block">
                {user.first_name || user.username}
              </span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  ROLE_COLORS[user.role] ?? 'bg-gray-100 text-gray-700'
                }`}
              >
                {ROLE_LABELS[user.role] ?? user.role}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-100"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
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
