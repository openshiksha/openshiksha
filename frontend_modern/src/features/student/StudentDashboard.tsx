import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { AssignmentList } from './AssignmentList';
import { useAssignments } from './useAssignments';
import { useStreak } from './useStreak';
import { StreakBadge } from './StreakBadge';
import { RecommendationsPanel } from './RecommendationsPanel';
import { DueForReviewPanel } from './DueForReviewPanel';

export const StudentDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: assignments, isLoading, isError } = useAssignments();
  const { data: streak } = useStreak();

  const greeting = user?.first_name ? `Hi, ${user.first_name}!` : 'Your Dashboard';

  return (
    <div>
      {/* Page header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 truncate">{greeting}</h1>
          {streak ? (
            <StreakBadge
              streak={streak.current_streak}
              tier={streak.milestone_tier}
              longestStreak={streak.longest_streak}
              graceUsed={streak.streak_grace_used}
            />
          ) : (
            <p className="text-gray-500 mt-1 text-sm sm:text-base">Here are your assignments</p>
          )}
        </div>
        <button
          onClick={() => navigate('/student/proficiency')}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium whitespace-nowrap shrink-0 mt-1"
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

      <RecommendationsPanel />
      <DueForReviewPanel />
    </div>
  );
};
