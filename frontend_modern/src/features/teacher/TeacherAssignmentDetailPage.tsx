import { useParams, useNavigate } from 'react-router-dom';
import { useTeacherAssignmentDetail } from './useTeacherAssignmentDetail';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { SubmissionWithStudent } from './useTeacherAssignmentDetail';

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

const isOverdue = (dueAt: string) => new Date(dueAt) < new Date();

const ScoreBadge = ({ score }: { score: number | null }) => {
  if (score === null) {
    return <span className="text-xs text-gray-400 italic">Grading...</span>;
  }
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? 'text-green-600' : pct >= 40 ? 'text-yellow-600' : 'text-red-600';
  return <span className={`text-sm font-semibold ${color}`}>{pct}%</span>;
};

const SubmissionRow = ({ sub }: { sub: SubmissionWithStudent }) => (
  <tr className="border-t border-gray-100 hover:bg-gray-50 transition-colors">
    <td className="px-4 py-3 text-sm text-gray-900">{sub.student_name}</td>
    <td className="px-4 py-3 text-sm text-gray-500">
      {sub.submitted_at ? formatDate(sub.submitted_at) : <span className="text-gray-300">—</span>}
    </td>
    <td className="px-4 py-3">
      {sub.submitted_at ? (
        <ScoreBadge score={sub.score} />
      ) : (
        <span className="text-xs text-gray-400">—</span>
      )}
    </td>
    <td className="px-4 py-3">
      {sub.submitted_at ? (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
          ✓ Submitted
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
          ⏳ Pending
        </span>
      )}
    </td>
  </tr>
);

export const TeacherAssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const assignmentId = id ? parseInt(id, 10) : 0;

  const { metaQuery, submissionsQuery } = useTeacherAssignmentDetail(assignmentId);

  const isLoading = metaQuery.isLoading || submissionsQuery.isLoading;
  const isError = metaQuery.isError || submissionsQuery.isError;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError || !metaQuery.data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 text-center text-gray-500">
        <p>Failed to load assignment. It may not exist or you may not have access.</p>
        <button onClick={() => navigate('/teacher')} className="mt-4 text-indigo-600 hover:underline text-sm">
          ← Back to dashboard
        </button>
      </div>
    );
  }

  const assignment = metaQuery.data;
  const submissions = submissionsQuery.data ?? [];

  const submittedCount = submissions.filter((s) => s.submitted_at).length;
  const totalStudents = assignment.student_count;
  const avgScore = assignment.average_score;
  const dueDate = new Date(assignment.due_at).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
  const overdue = isOverdue(assignment.due_at);
  const submissionPct = totalStudents > 0 ? (submittedCount / totalStudents) * 100 : 0;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Back link */}
      <button
        onClick={() => navigate('/teacher')}
        className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
      >
        ← Back to dashboard
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h1 className="text-xl font-bold text-gray-900">{assignment.problem_set.title}</h1>
        <p className="text-sm text-gray-500 mt-1">{assignment.subject_room_display}</p>

        <div className="flex flex-wrap gap-4 mt-4 text-sm">
          <div>
            <span className="text-gray-400">Due</span>{' '}
            <span className={`font-medium ${overdue ? 'text-red-500' : 'text-gray-700'}`}>
              {dueDate}{overdue ? ' (overdue)' : ''}
            </span>
          </div>
          <div>
            <span className="text-gray-400">Submitted</span>{' '}
            <span className="font-medium text-gray-700">
              {submittedCount}/{totalStudents}
            </span>
          </div>
          {avgScore !== null && (
            <div>
              <span className="text-gray-400">Avg score</span>{' '}
              <span className="font-medium text-gray-700">{Math.round(avgScore * 100)}%</span>
            </div>
          )}
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all"
              style={{ width: `${submissionPct}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">{Math.round(submissionPct)}% submitted</p>
        </div>
      </div>

      {/* Submissions table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-800">Student Submissions</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {submissions.length} submission{submissions.length !== 1 ? 's' : ''} recorded
            {totalStudents > submissions.length && (
              <> · {totalStudents - submissions.length} students have not started</>
            )}
          </p>
        </div>

        {submissions.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-sm">No submissions yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Submitted</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((sub) => (
                  <SubmissionRow key={sub.id} sub={sub} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
