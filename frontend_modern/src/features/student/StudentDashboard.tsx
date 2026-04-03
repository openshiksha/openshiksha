import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { AssignmentList } from './AssignmentList';
import { useAssignments } from './useAssignments';

export const StudentDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: assignments, isLoading, isError } = useAssignments();

  const greeting = user?.first_name ? `Hi, ${user.first_name}!` : 'Your Dashboard';

  return (
    <div>
      {/* Page header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{greeting}</h1>
          <p className="text-gray-500 mt-1">Here are your assignments</p>
        </div>
        <button
          onClick={() => navigate('/student/proficiency')}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium whitespace-nowrap"
        >
          My Progress →
        </button>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {isError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          Failed to load assignments. Please refresh the page.
        </div>
      )}

      {assignments && (
        <AssignmentList assignments={assignments} />
      )}
    </div>
  );
};
