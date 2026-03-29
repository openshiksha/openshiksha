import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './shared/hooks/useAuth';

// Placeholder components - will be implemented in phases
const LoginPage = () => <div className="p-4">Login Page - Coming Soon</div>;
const StudentDashboard = () => <div className="p-4">Student Dashboard - Coming Soon</div>;
const TeacherDashboard = () => <div className="p-4">Teacher Dashboard - Coming Soon</div>;
const NotFound = () => <div className="p-4">404 - Page Not Found</div>;

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route
            path="/student/*"
            element={isAuthenticated ? <StudentDashboard /> : <Navigate to="/login" />}
          />
          <Route
            path="/teacher/*"
            element={isAuthenticated ? <TeacherDashboard /> : <Navigate to="/login" />}
          />

          {/* Default route */}
          <Route
            path="/"
            element={isAuthenticated ? <Navigate to="/student" /> : <Navigate to="/login" />}
          />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
