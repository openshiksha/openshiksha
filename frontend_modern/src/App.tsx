import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './shared/hooks/useAuth';
import { LoginPage } from './features/auth/LoginPage';
import { RegisterPage } from './features/auth/RegisterPage';
import { RegisterSchoolPage } from './features/auth/RegisterSchoolPage';
import { RegisterOpenPage } from './features/auth/RegisterOpenPage';
import { HomePage } from './features/home/HomePage';
import { AppShell } from './features/layout/AppShell';
import { ProtectedRoute } from './features/layout/ProtectedRoute';
import { NotFoundPage } from './features/shared/NotFoundPage';
import { UserRole } from './types/index';
import { LoadingSpinner } from './shared/components/LoadingSpinner';
import { ErrorBoundary } from './shared/ui';
import { I18nProvider } from './shared/i18n';

// Route-level code-splitting. Every page below is loaded on demand so a cold
// open of /login (the K-12 student's first impression on a budget Android phone)
// never downloads the teacher authoring surface, the admin classroom manager,
// or the dev-only widget playground. Auth + home stay eager because they sit on
// the critical first-paint path. See docs/initiatives/performance-budget.md.
const lazyNamed = <T extends Record<string, unknown>, K extends keyof T>(
  loader: () => Promise<T>,
  name: K,
): T[K] extends React.ComponentType<infer P> ? React.LazyExoticComponent<React.ComponentType<P>> : never =>
  lazy(() => loader().then((m) => ({ default: m[name] as unknown as React.ComponentType<unknown> }))) as never;

const EnquirePage = lazyNamed(() => import('./features/enquiry/EnquirePage'), 'EnquirePage');
const DesignSystemPage = lazyNamed(() => import('./features/design/DesignSystemPage'), 'DesignSystemPage');
const WidgetDevPage = lazyNamed(() => import('./features/widgets/WidgetDevPage'), 'WidgetDevPage');
const StudentDashboard = lazyNamed(() => import('./features/student/StudentDashboard'), 'StudentDashboard');
const AssignmentDetailPage = lazyNamed(() => import('./features/student/AssignmentDetailPage'), 'AssignmentDetailPage');
const ProficiencyPage = lazyNamed(() => import('./features/student/ProficiencyPage'), 'ProficiencyPage');
const LearningPathPage = lazyNamed(() => import('./features/student/LearningPathPage'), 'LearningPathPage');
const SRSDrillPage = lazyNamed(() => import('./features/student/SRSDrillPage'), 'SRSDrillPage');
const BrowsePage = lazyNamed(() => import('./features/student/BrowsePage'), 'BrowsePage');
const BrowsePracticePage = lazyNamed(() => import('./features/student/BrowsePracticePage'), 'BrowsePracticePage');
const ProfilePage = lazyNamed(() => import('./features/shared/ProfilePage'), 'ProfilePage');
const TeacherDashboard = lazyNamed(() => import('./features/teacher/TeacherDashboard'), 'TeacherDashboard');
const CreateAssignmentPage = lazyNamed(() => import('./features/teacher/CreateAssignmentPage'), 'CreateAssignmentPage');
const CreateQuestionPage = lazyNamed(() => import('./features/teacher/CreateQuestionPage'), 'CreateQuestionPage');
const CreateProblemSetPage = lazyNamed(() => import('./features/teacher/CreateProblemSetPage'), 'CreateProblemSetPage');
const ProblemSetPreviewPage = lazyNamed(() => import('./features/teacher/ProblemSetPreviewPage'), 'ProblemSetPreviewPage');
const ProblemSetVersionsPage = lazyNamed(() => import('./features/teacher/ProblemSetVersionsPage'), 'ProblemSetVersionsPage');
const TeacherAssignmentDetailPage = lazyNamed(() => import('./features/teacher/TeacherAssignmentDetailPage'), 'TeacherAssignmentDetailPage');
const QuestionBankPage = lazyNamed(() => import('./features/teacher/QuestionBankPage'), 'QuestionBankPage');
const OpenResponseGradingPage = lazyNamed(() => import('./features/teacher/OpenResponseGradingPage'), 'OpenResponseGradingPage');
const ParentDashboard = lazyNamed(() => import('./features/parent/ParentDashboard'), 'ParentDashboard');
const ParentInsightsPage = lazyNamed(() => import('./features/parent/ParentInsightsPage'), 'ParentInsightsPage');
const ParentInsightsLandingPage = lazyNamed(() => import('./features/parent/ParentInsightsLandingPage'), 'ParentInsightsLandingPage');
const AdminDashboard = lazyNamed(() => import('./features/admin/AdminDashboard'), 'AdminDashboard');
const ClassroomManagePage = lazyNamed(() => import('./features/admin/ClassroomManagePage'), 'ClassroomManagePage');

function RouteFallback() {
  return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <LoadingSpinner size="lg" />
    </div>
  );
}

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
    ? user?.role === 'teacher' ? '/teacher'
    : user?.role === 'parent' ? '/parent'
    : user?.role === 'admin' ? '/admin'
    : user?.role === 'open_student' ? '/student/browse'
    : '/student'
    : '/login';

  return (
    <I18nProvider>
    <Router>
      <ErrorBoundary>
      <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/register/school" element={<RegisterSchoolPage />} />
        <Route path="/register/open" element={<RegisterOpenPage />} />
        <Route path="/enquire" element={<EnquirePage />} />
        <Route path="/design" element={<DesignSystemPage />} />
        <Route path="/widgets/dev" element={<WidgetDevPage />} />

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
          path="/student/learning-path"
          element={
            <ProtectedRoute>
              <AppShell>
                <LearningPathPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/srs-drill/:entryId"
          element={
            <ProtectedRoute>
              <AppShell>
                <SRSDrillPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/browse"
          element={
            <ProtectedRoute>
              <AppShell>
                <BrowsePage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/browse/chapter/:chapterId"
          element={
            <ProtectedRoute>
              <AppShell>
                <BrowsePracticePage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <AppShell>
                <ProfilePage />
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
          path="/teacher/problem-sets/:id/preview"
          element={
            <ProtectedRoute>
              <AppShell>
                <ProblemSetPreviewPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/problem-sets/:id/versions"
          element={
            <ProtectedRoute>
              <AppShell>
                <ProblemSetVersionsPage />
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

        <Route
          path="/teacher/questions"
          element={
            <ProtectedRoute>
              <AppShell>
                <QuestionBankPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/grading"
          element={
            <ProtectedRoute>
              <AppShell>
                <OpenResponseGradingPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher/questions/:id/edit"
          element={
            <ProtectedRoute>
              <AppShell>
                <CreateQuestionPage editMode={true} />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/parent"
          element={
            <ProtectedRoute>
              <AppShell>
                <ParentDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/parent/insights"
          element={
            <ProtectedRoute allowedRoles={[UserRole.PARENT]}>
              <AppShell>
                <ParentInsightsLandingPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/parent/insights/:childId"
          element={
            <ProtectedRoute allowedRoles={[UserRole.PARENT]}>
              <AppShell>
                <ParentInsightsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
              <AppShell>
                <AdminDashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/classrooms/:id"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
              <AppShell>
                <ClassroomManagePage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route path="/" element={isAuthenticated ? <Navigate to={defaultPath} replace /> : <HomePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </Suspense>
      </ErrorBoundary>
    </Router>
    </I18nProvider>
  );
}

export default App;
