import { useAuth } from '@/shared/hooks/useAuth';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { AssignmentList } from './AssignmentList';
import { useAssignments } from './useAssignments';

export const StudentDashboard = () => {
  const { user } = useAuth();
  const { data: assignments, isLoading, isError } = useAssignments();

  const greeting = user?.first_name ? `Hi, ${user.first_name}!` : 'Your Dashboard';

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{greeting}</h1>
        <p className="text-gray-500 mt-1">Here are your assignments</p>
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
