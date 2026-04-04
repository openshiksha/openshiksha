import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './shared/hooks/useAuth';
import { LoginPage } from './features/auth/LoginPage';
import { AppShell } from './features/layout/AppShell';
import { ProtectedRoute } from './features/layout/ProtectedRoute';
import { StudentDashboard } from './features/student/StudentDashboard';
import { AssignmentDetailPage } from './features/student/AssignmentDetailPage';
import { ProficiencyPage } from './features/student/ProficiencyPage';
import { TeacherDashboard } from './features/teacher/TeacherDashboard';
import { CreateAssignmentPage } from './features/teacher/CreateAssignmentPage';
import { CreateQuestionPage } from './features/teacher/CreateQuestionPage';
import { CreateProblemSetPage } from './features/teacher/CreateProblemSetPage';
import { TeacherAssignmentDetailPage } from './features/teacher/TeacherAssignmentDetailPage';
import { LoadingSpinner } from './shared/components/LoadingSpinner';

const NotFound = () => (
  <div className="text-center py-16">
    <h2 className="text-2xl font-semibold text-gray-700">404 - Page Not Found</h2>
  </div>
);

function App() {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const defaultPath = isAuthenticated
    ? user?.role === 'teacher' ? '/teacher' : '/student'
    : '/login';

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/student"
          element={
            <ProtectedRoute>
              <AppShell>
                <StudentDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/assignments/:id"
          element={
            <ProtectedRoute>
              <AppShell>
                <AssignmentDetailPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher"
          element={
            <ProtectedRoute>
              <AppShell>
                <TeacherDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/proficiency"
          element={
            <ProtectedRoute>
              <AppShell>
                <ProficiencyPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/assignments/new"
          element={
            <ProtectedRoute>
              <AppShell>
                <CreateAssignmentPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/questions/new"
          element={
            <ProtectedRoute>
              <AppShell>
                <CreateQuestionPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/problem-sets/new"
          element={
            <ProtectedRoute>
              <AppShell>
                <CreateProblemSetPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/assignments/:id"
          element={
            <ProtectedRoute>
              <AppShell>
                <TeacherAssignmentDetailPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to={defaultPath} replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
