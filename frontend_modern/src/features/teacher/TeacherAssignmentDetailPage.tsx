import { useParams, useNavigate } from 'react-router-dom';
import { useTeacherAssignmentDetail } from './useTeacherAssignmentDetail';
import { useQuestionMistakes } from './useQuestionMistakes';
import { AssignmentSnapshotPreview } from './AssignmentSnapshotPreview';
import {
  Badge,
  EmptyState,
  LoadingSpinner,
  SectionHeading,
  Stat,
  ResponsiveTable,
  type ResponsiveColumn,
} from '@/shared/ui';
import { useI18n, useFormat, type Translate } from '@/shared/i18n';
import type { SubmissionWithStudent } from './useTeacherAssignmentDetail';
import type { QuestionMistake } from './useQuestionMistakes';

const isOverdue = (dueAt: string) => new Date(dueAt) < new Date();

const ScoreBadge = ({ score, t }: { score: number | null; t: Translate }) => {
  if (score === null) {
    return <span className="text-xs italic text-ink-400">{t('teacher.adGrading')}</span>;
  }
  const pct = Math.round(score * 100);
  const tone = pct >= 70 ? 'text-emerald-700' : pct >= 40 ? 'text-amber-700' : 'text-rose-700';
  return <span className={`text-sm font-semibold ${tone}`}>{pct}%</span>;
};

const HardestQuestionsPanel = ({ mistakes }: { mistakes: QuestionMistake[] }) => {
  const { t } = useI18n();
  if (!mistakes.length) return null;
  const maxRegression = Math.max(...mistakes.map((m) => m.regression));
  return (
    <div className="os-card mt-6 p-5">
      <h3 className="mb-3 font-display text-base font-semibold text-ink-900">
        {t('teacher.adHardestTitle')}{' '}
        <span className="font-normal text-ink-400">{t('teacher.adHardestSub')}</span>
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
              {t('teacher.adPtsLost', { pts: m.regression.toFixed(1) })}
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
  const { t } = useI18n();
  const { formatDate } = useFormat();
  const assignmentId = id ? parseInt(id, 10) : 0;

  const submissionDateOpts: Intl.DateTimeFormatOptions = {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  };

  const { metaQuery, submissionsQuery } = useTeacherAssignmentDetail(assignmentId);
  const { data: mistakes } = useQuestionMistakes(metaQuery.data?.subject_room);

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
          title={t('teacher.adLoadFailTitle')}
          description={t('teacher.adLoadFailDesc')}
          action={
            <button
              onClick={() => navigate('/teacher')}
              className="rounded text-sm font-semibold text-brand-700 hover:text-brand-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              ← {t('teacher.adBackToDashboard')}
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
  const dueDate = formatDate(assignment.due_at);
  const overdue = isOverdue(assignment.due_at);
  const submissionPct = totalStudents > 0 ? (submittedCount / totalStudents) * 100 : 0;

  const submissionColumns: ResponsiveColumn<SubmissionWithStudent>[] = [
    {
      key: 'student',
      header: t('teacher.adThStudent'),
      primary: true,
      cell: (sub) => <span className="font-medium text-ink-900">{sub.student_name}</span>,
    },
    {
      key: 'submitted',
      header: t('teacher.adThSubmitted'),
      cell: (sub) =>
        sub.submitted_at ? (
          <span className="text-ink-500">{formatDate(sub.submitted_at, submissionDateOpts)}</span>
        ) : (
          <span className="text-ink-300">—</span>
        ),
    },
    {
      key: 'score',
      header: t('teacher.adThScore'),
      align: 'right',
      cell: (sub) =>
        sub.submitted_at ? (
          <ScoreBadge score={sub.score} t={t} />
        ) : (
          <span className="text-xs text-ink-400">—</span>
        ),
    },
    {
      key: 'status',
      header: t('teacher.adThStatus'),
      align: 'right',
      cell: (sub) =>
        sub.submitted_at ? (
          <Badge tone="success">✓ {t('teacher.adBadgeSubmitted')}</Badge>
        ) : (
          <Badge tone="attention">⏳ {t('teacher.adBadgePending')}</Badge>
        ),
    },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <button
        onClick={() => navigate('/teacher')}
        className="flex items-center gap-1 rounded text-sm text-ink-500 transition-colors hover:text-ink-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        ← {t('teacher.adBackToDashboard')}
      </button>

      <div className="os-card p-6">
        <SectionHeading
          as="h1"
          eyebrow={assignment.subject_room_display}
          title={assignment.problem_set.title}
          action={
            overdue ? (
              <Badge tone="urgent">{t('teacher.adOverdue')}</Badge>
            ) : (
              <Badge tone="brand">{t('teacher.adActive')}</Badge>
            )
          }
        />

        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Stat
            label={t('teacher.adStatDue')}
            value={dueDate}
            delta={overdue ? t('teacher.adOverdue') : undefined}
            tone="urgent"
          />
          <Stat
            label={t('teacher.adStatSubmitted')}
            value={`${submittedCount}/${totalStudents}`}
          />
          {avgScore !== null && (
            <Stat label={t('teacher.adStatAvg')} value={`${Math.round(avgScore * 100)}%`} />
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
          <p className="mt-1 text-xs text-ink-400">
            {t('teacher.adSubmittedPct', { pct: Math.round(submissionPct) })}
          </p>
        </div>
      </div>

      <AssignmentSnapshotPreview
        assignmentId={assignment.id}
        problemSet={assignment.problem_set}
        snapshotDrift={assignment.snapshot_drift === true}
        hasResyncHistory={assignment.has_resync_history === true}
      />

      <div className="os-card p-0">
        <div className="border-b border-ink-100 px-6 py-4">
          <h2 className="font-display text-base font-semibold text-ink-900">
            {t('teacher.adSubmissionsTitle')}
          </h2>
          <p className="mt-0.5 text-xs text-ink-400">
            {t(
              submissions.length === 1
                ? 'teacher.adSubmissionsRecordedOne'
                : 'teacher.adSubmissionsRecordedMany',
              { count: submissions.length },
            )}
            {totalStudents > submissions.length && (
              <> · {t('teacher.adNotStarted', { count: totalStudents - submissions.length })}</>
            )}
          </p>
        </div>

        {submissions.length === 0 ? (
          <div className="px-6 py-12">
            <EmptyState title={t('teacher.adNoSubmissions')} />
          </div>
        ) : (
          <div className="px-4 py-2 sm:px-6 sm:py-3">
            <ResponsiveTable
              aria-label={t('teacher.adSubmissionsTitle')}
              rows={submissions}
              rowKey={(sub) => sub.id}
              columns={submissionColumns}
            />
          </div>
        )}
      </div>

      <HardestQuestionsPanel mistakes={mistakes ?? []} />
    </div>
  );
};
