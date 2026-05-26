import { Link } from 'react-router-dom';

export const RegisterPage = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div className="w-full max-w-md">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4 shadow-lg">
          <span className="text-white text-2xl font-bold">OS</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900">Create Account</h1>
        <p className="text-gray-500 mt-1">How would you like to learn?</p>
      </div>

      <div className="space-y-4">
        <Link
          to="/register/school"
          className="block w-full bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-100 group"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-indigo-100 transition-colors">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">
                Join a School
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Use a classroom join code from your teacher to enroll automatically.
              </p>
            </div>
          </div>
        </Link>

        <Link
          to="/register/open"
          className="block w-full bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-100 group"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-emerald-100 transition-colors">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors">
                Study Independently
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Practice from the shared question bank at your own pace — no school needed.
              </p>
            </div>
          </div>
        </Link>
      </div>

      <p className="text-center text-sm text-gray-500 mt-6">
        Already have an account?{' '}
        <Link to="/login" className="text-indigo-600 hover:text-indigo-800 font-medium">
          Sign in
        </Link>
      </p>
    </div>
  </div>
);
