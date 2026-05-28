import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { useLoginMutation } from './useLoginMutation';

export const LoginPage = () => {
  const { isAuthenticated, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const loginMutation = useLoginMutation();

  // Already logged in — redirect to role home
  if (isAuthenticated && user) {
    return <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} replace />;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md">
        {/* Logo + Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4 shadow-lg">
            <span className="text-white text-2xl font-bold">OS</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">OpenShiksha</h1>
          <p className="text-gray-500 mt-1">Sign in to continue learning</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} noValidate>
            <div className="space-y-5">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                  placeholder="Enter your username"
                  disabled={loginMutation.isPending}
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                  placeholder="Enter your password"
                  disabled={loginMutation.isPending}
                />
              </div>

              {/* Error message */}
              {loginMutation.isError && (
                <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
                  Invalid username or password. Please try again.
                </div>
              )}

              <button
                type="submit"
                disabled={loginMutation.isPending || !username || !password}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                {loginMutation.isPending ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Signing in…
                  </span>
                ) : (
                  'Sign in'
                )}
              </button>
            </div>
          </form>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-indigo-600 hover:text-indigo-800 font-medium">
            Register
          </Link>
        </p>
        <p className="text-center text-sm text-gray-500 mt-2">
          Are you a school?{' '}
          <Link to="/enquire" className="text-indigo-600 hover:text-indigo-800 font-medium">
            Enquire about OpenShiksha
          </Link>
        </p>
        <p className="text-center text-xs text-gray-400 mt-2">
          OpenShiksha © {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
};
