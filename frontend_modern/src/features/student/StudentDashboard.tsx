import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { Button, EmptyState } from '@/shared/ui';
import { AssignmentList } from './AssignmentList';
import { useAssignments } from './useAssignments';
import { useStreak } from './useStreak';
import { StreakBadge } from './StreakBadge';
import { RecommendationsPanel } from './RecommendationsPanel';
import { DueForReviewPanel } from './DueForReviewPanel';
import { AnnouncementsBanner } from './AnnouncementsBanner';
import { UserRole } from '@/types/index';

export const StudentDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: assignments, isLoading, isError } = useAssignments();
  const { data: streak } = useStreak();

  const greeting = user?.first_name ? `Hi, ${user.first_name}!` : 'Your dashboard';

  return (
    <div>
      {/* Page header */}
      <div className="mb-6 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-display text-3xl font-semibold text-ink-900 truncate">{greeting}</h1>
          {streak ? (
            <div className="mt-2">
              <StreakBadge
                streak={streak.current_streak}
                tier={streak.milestone_tier}
                longestStreak={streak.longest_streak}
                graceUsed={streak.streak_grace_used}
              />
            </div>
          ) : (
            <p className="mt-1 text-sm text-ink-500 sm:text-base">Here are your assignments.</p>
          )}
        </div>
        <button
          onClick={() => navigate('/student/proficiency')}
          className="shrink-0 whitespace-nowrap text-sm font-semibold text-brand-700 hover:text-brand-800"
        >
          My progress →
        </button>
      </div>

      {/* Announcements */}
      <AnnouncementsBanner />

      {/* Content */}
      {isLoading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {isError && (
        <div
          className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
          role="alert"
        >
          Failed to load assignments. Please refresh the page.
        </div>
      )}

      {assignments && assignments.length === 0 && user?.role === UserRole.OPEN_STUDENT && (
        <EmptyState
          title="You're not enrolled in a classroom yet"
          description="Browse the shared question bank to start practising on your own."
          action={
            <Button onClick={() => navigate('/student/browse')}>Browse subjects →</Button>
          }
        />
      )}

      {/*
        The major dashboard surfaces are separated by the same 32 px (mt-8)
        gutter the V2 spacing scale uses elsewhere. Without it the
        "Due Soon" assignment cards sit flush against the recommendations
        panel, which read as one merged block rather than discrete
        sections (regression spotted on the live student view).
      */}
      <div className="space-y-8">
        {assignments && assignments.length > 0 && <AssignmentList assignments={assignments} />}
        <RecommendationsPanel />
        <DueForReviewPanel />
      </div>
    </div>
  );
};
