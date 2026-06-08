import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTeacherAssignmentDetail } from './useTeacherAssignmentDetail';
import { useQuestionMistakes } from './useQuestionMistakes';
import {
  Badge,
  Button,
  EmptyState,
  LoadingSpinner,
  SectionHeading,
  Stat,
} from '@/shared/ui';
import type { SubmissionWithStudent } from './useTeacherAssignmentDetail';
import type { QuestionMistake } from './useQuestionMistakes';

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });

const isOverdue = (dueAt: string) => new Date(dueAt) < new Date();

const ScoreBadge = ({ score }: { score: number | null }) => {
  if (score === null) {
    return <span className="text-xs italic text-ink-400">Grading...</span>;
  }
  const pct = Math.round(score * 100);
  const tone = pct >= 70 ? 'text-emerald-700' : pct >= 40 ? 'text-amber-700' : 'text-rose-700';
  return <span className={`text-sm font-semibold ${tone}`}>{pct}%</span>;
};

const SubmissionRow = ({ sub }: { sub: SubmissionWithStudent }) => (
  <tr className="border-t border-ink-100 transition-colors hover:bg-brand-50/40">
    <td className="px-4 py-3 text-sm font-medium text-ink-900">{sub.student_name}</td>
    <td className="px-4 py-3 text-sm text-ink-500">
      {sub.submitted_at ? formatDate(sub.submitted_at) : <span className="text-ink-300">—</span>}
    </td>
    <td className="px-4 py-3">
      {sub.submitted_at ? (
        <ScoreBadge score={sub.score} />
      ) : (
        <span className="text-xs text-ink-400">—</span>
      )}
    </td>
    <td className="px-4 py-3">
      {sub.submitted_at ? (
        <Badge tone="success">✓ Submitted</Badge>
      ) : (
        <Badge tone="attention">⏳ Pending</Badge>
      )}
    </td>
  </tr>
);

const HardestQuestionsPanel = ({ mistakes }: { mistakes: QuestionMistake[] }) => {
  if (!mistakes.length) return null;
  const maxRegression = Math.max(...mistakes.map((m) => m.regression));
  return (
    <div className="os-card mt-6 p-5">
      <h3 className="mb-3 font-display text-base font-semibold text-ink-900">
        Hardest Questions{' '}
        <span className="font-normal text-ink-400">(by cumulative marks lost)</span>
      </h3>
      <div className="space-y-3">
        {mistakes.slice(0, 5).map((m) => (
          <div key={m.id} className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <p className="line-clamp-2 text-xs text-ink-700">{m.question_text}</p>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-ink-100">
                <div
                  className="h-full rounded-full bg-rose-500"
                  style={{ width: `${Math.round((m.regression / maxRegression) * 100)}%` }}
                />
              </div>
            </div>
            <span className="shrink-0 text-xs font-semibold text-rose-700">
              {m.regression.toFixed(1)} pts lost
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const TeacherAssignmentDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const assignmentId = id ? parseInt(id, 10) : 0;

  const { metaQuery, submissionsQuery, updateDueAtMutation, closeMutation, reopenMutation } =
    useTeacherAssignmentDetail(assignmentId);
  const { data: mistakes } = useQuestionMistakes(metaQuery.data?.subject_room);

  // Draft holds the user's edit; null means "show server value".
  // datetime-local input expects "YYYY-MM-DDTHH:mm" in local time.
  const [dueAtDraft, setDueAtDraft] = useState<string | null>(null);
  const serverDueAtLocal = (() => {
    const dueAt = metaQuery.data?.due_at;
    if (!dueAt) return '';
    const d = new Date(dueAt);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  })();
  const dueAtValue = dueAtDraft ?? serverDueAtLocal;

  const isLoading = metaQuery.isLoading || submissionsQuery.isLoading;
  const isError = metaQuery.isError || submissionsQuery.isError;

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError || !metaQuery.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <EmptyState
          title="Failed to load assignment"
          description="It may not exist or you may not have access."
          action={
            <button
              onClick={() => navigate('/teacher')}
              className="rounded text-sm font-semibold text-brand-700 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              ← Back to dashboard
            </button>
          }
        />
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
  const status = assignment.status ?? (overdue ? 'overdue' : 'active');
  const isClosed = status === 'closed';

  const statusBadge = isClosed ? (
    <Badge tone="neutral">Closed</Badge>
  ) : status === 'overdue' ? (
    <Badge tone="urgent">Overdue</Badge>
  ) : (
    <Badge tone="brand">Active</Badge>
  );

  const handleDueAtSave = () => {
    if (!dueAtValue) return;
    const iso = new Date(dueAtValue).toISOString();
    updateDueAtMutation.mutate(iso, {
      onSuccess: () => setDueAtDraft(null),
    });
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <button
        onClick={() => navigate('/teacher')}
        className="flex items-center gap-1 rounded text-sm text-ink-500 transition-colors hover:text-ink-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        ← Back to dashboard
      </button>

      <div className="os-card p-6">
        <SectionHeading
          as="h1"
          eyebrow={assignment.subject_room_display}
          title={assignment.problem_set.title}
          action={statusBadge}
        />

        {/* Lifecycle controls — due-date edit + close / reopen */}
        <div
          className="mt-5 flex flex-wrap items-end gap-3 rounded-xl border border-ink-100 bg-paper-50 p-4"
          data-testid="lifecycle-controls"
        >
          <label className="flex flex-col text-xs font-semibold uppercase tracking-wide text-ink-500">
            Due date
            <input
              type="datetime-local"
              value={dueAtValue}
              onChange={(e) => setDueAtDraft(e.target.value)}
              disabled={isClosed || updateDueAtMutation.isPending}
              className="mt-1 rounded-lg border border-ink-200 bg-paper px-3 py-1.5 text-sm font-normal normal-case text-ink-900"
              data-testid="due-at-input"
            />
          </label>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDueAtSave}
            disabled={isClosed || updateDueAtMutation.isPending}
            data-testid="due-at-save"
          >
            {updateDueAtMutation.isPending ? 'Saving…' : 'Save due date'}
          </Button>
          <div className="ml-auto">
            {isClosed ? (
              <Button
                variant="brand"
                size="sm"
                onClick={() => reopenMutation.mutate()}
                disabled={reopenMutation.isPending}
                data-testid="reopen-button"
              >
                {reopenMutation.isPending ? 'Reopening…' : 'Reopen assignment'}
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => closeMutation.mutate()}
                disabled={closeMutation.isPending}
                data-testid="close-button"
              >
                {closeMutation.isPending ? 'Closing…' : 'Close assignment'}
              </Button>
            )}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Stat
            label="Due"
            value={dueDate}
            delta={overdue ? 'Overdue' : undefined}
            tone="urgent"
          />
          <Stat
            label="Submitted"
            value={`${submittedCount}/${totalStudents}`}
          />
          {avgScore !== null && (
            <Stat label="Avg score" value={`${Math.round(avgScore * 100)}%`} />
          )}
        </div>

        <div className="mt-5">
          <div
            className="h-2 overflow-hidden rounded-full bg-ink-100"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(submissionPct)}
          >
            <div
              className="h-full rounded-full bg-brand-600 transition-all"
              style={{ width: `${submissionPct}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-ink-400">{Math.round(submissionPct)}% submitted</p>
        </div>
      </div>

      <div className="os-card overflow-hidden p-0">
        <div className="border-b border-ink-100 px-6 py-4">
          <h2 className="font-display text-base font-semibold text-ink-900">
            Student Submissions
          </h2>
          <p className="mt-0.5 text-xs text-ink-400">
            {submissions.length} submission{submissions.length !== 1 ? 's' : ''} recorded
            {totalStudents > submissions.length && (
              <> · {totalStudents - submissions.length} students have not started</>
            )}
          </p>
        </div>

        {submissions.length === 0 ? (
          <div className="px-6 py-12">
            <EmptyState title="No submissions yet." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-ink-50 text-xs font-display font-semibold uppercase tracking-wide text-ink-500">
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

      <HardestQuestionsPanel mistakes={mistakes ?? []} />
    </div>
  );
};
