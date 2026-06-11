import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AIBadge, Badge, Button, EmptyState, Skeleton, isAIStub } from '@/shared/ui';
import { useSubjectRooms } from './useSubjectRooms';
import {
  gradeErrorDetail,
  useOpenGrades,
  useRegradeOpenGrade,
  useReviewOpenGrade,
  type OpenGradeStatus,
  type OpenResponseGrade,
} from './useOpenResponseGrading';

const STATUS_LABEL: Record<OpenGradeStatus, string> = {
  pending: 'AI grading…',
  ai_graded: 'Needs your review',
  reviewed: 'Finalised',
  failed: 'Grading failed',
};

const STATUS_TONE: Record<OpenGradeStatus, 'attention' | 'brand' | 'success' | 'urgent'> = {
  pending: 'attention',
  ai_graded: 'brand',
  reviewed: 'success',
  failed: 'urgent',
};

const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

interface ReviewFormProps {
  grade: OpenResponseGrade;
}

/**
 * The human-in-the-loop step: the teacher accepts or overrides the AI's
 * suggestion. Score defaults to the suggestion so accepting is one click.
 */
const ReviewForm = ({ grade }: ReviewFormProps) => {
  const review = useReviewOpenGrade();
  const [score, setScore] = useState(
    grade.suggested_score != null ? String(grade.suggested_score) : ''
  );
  const [comment, setComment] = useState('');

  const parsed = Number(score);
  const valid = score !== '' && !Number.isNaN(parsed) && parsed >= 0 && parsed <= grade.max_marks;

  return (
    <form
      className="mt-3 rounded-lg border border-ink-100 bg-ink-50/60 p-3 space-y-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (!valid) return;
        review.mutate({
          id: grade.id,
          final_score: parsed,
          teacher_comment: comment.trim() || undefined,
        });
      }}
    >
      <div className="flex flex-wrap items-end gap-3">
        <label className="block text-xs text-ink-600">
          Final marks (out of {grade.max_marks})
          <input
            type="number"
            min={0}
            max={grade.max_marks}
            step={0.5}
            value={score}
            onChange={(e) => setScore(e.target.value)}
            className="input-brand mt-1 block w-24 text-sm"
          />
        </label>
        <label className="block flex-1 min-w-[12rem] text-xs text-ink-600">
          Comment for the student <span className="text-ink-400">(optional)</span>
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="e.g. Good reasoning — name the process next time."
            className="input-brand mt-1 block w-full text-sm"
          />
        </label>
      </div>

      {review.isError && (
        <p className="text-xs text-rose-600">
          {gradeErrorDetail(review.error) ??
            "Couldn't save the grade just now. Please try again in a moment."}
        </p>
      )}

      <div className="flex items-center gap-2 pt-1">
        <Button type="submit" variant="brand" size="sm" disabled={!valid || review.isPending}>
          {review.isPending
            ? 'Saving…'
            : grade.suggested_score != null && parsed === grade.suggested_score
              ? 'Accept suggestion'
              : 'Save final grade'}
        </Button>
        <p className="text-xs text-ink-400">Finalising locks this grade.</p>
      </div>
    </form>
  );
};

const GradeCard = ({ grade }: { grade: OpenResponseGrade }) => {
  const regrade = useRegradeOpenGrade();
  const isStub = isAIStub(grade.model_used);

  return (
    <div className="os-card p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-lg text-ink-900 leading-tight">{grade.student_name}</p>
          <p className="mt-0.5 text-xs text-ink-500">
            {grade.subject_name} · submitted {formatDate(grade.created_at)}
          </p>
        </div>
        <Badge tone={STATUS_TONE[grade.status]} className="shrink-0">
          {STATUS_LABEL[grade.status]}
        </Badge>
      </div>

      <p className="mt-3 text-xs text-ink-500">
        <span className="font-semibold">Question:</span> {grade.question_text}
      </p>
      <blockquote className="mt-2 rounded-lg border border-ink-100 bg-ink-50/60 p-3 text-sm text-ink-800 leading-relaxed whitespace-pre-line">
        {grade.response_text}
      </blockquote>

      {grade.status === 'pending' && (
        <div className="mt-3 flex items-center gap-2">
          <span
            className="inline-block h-2 w-2 animate-pulse rounded-full bg-brand-500"
            aria-hidden
          />
          <p className="text-sm text-ink-600">AI is reading this response…</p>
        </div>
      )}

      {grade.status === 'failed' && (
        <div className="mt-3">
          <p className="text-sm text-rose-700">Couldn&apos;t grade this response.</p>
          {grade.error_detail && <p className="mt-1 text-xs text-ink-500">{grade.error_detail}</p>}
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            disabled={regrade.isPending}
            onClick={() => regrade.mutate({ id: grade.id })}
          >
            {regrade.isPending ? 'Retrying…' : 'Try again'}
          </Button>
        </div>
      )}

      {grade.status === 'ai_graded' && (
        <div className="mt-3">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-ink-900">
              AI suggests {grade.suggested_score}/{grade.max_marks}
            </p>
            {grade.confidence != null && (
              <span className="text-xs text-ink-400">
                {Math.round(grade.confidence * 100)}% confident
              </span>
            )}
            <AIBadge modelUsed={grade.model_used} stubLabel="Auto-graded" />
          </div>
          {grade.feedback && (
            <p className="mt-1.5 text-sm text-ink-700 leading-relaxed">{grade.feedback}</p>
          )}
          {isStub && (
            <p className="mt-1 text-xs text-ink-400">
              AI was unavailable, so this suggestion came from a keyword match against the model
              answer — please review with extra care.
            </p>
          )}

          {grade.criterion_scores.length > 0 && (
            <ul className="mt-2 space-y-1">
              {grade.criterion_scores.map((c) => (
                <li key={c.label} className="flex items-start gap-2 text-xs text-ink-600">
                  <span className="shrink-0 rounded-full bg-ink-100 px-2 py-0.5 font-medium text-ink-700">
                    {c.awarded}/{c.max}
                  </span>
                  <span>
                    <span className="font-semibold">{c.label}</span>
                    {c.comment && <> — {c.comment}</>}
                  </span>
                </li>
              ))}
            </ul>
          )}

          <ReviewForm grade={grade} />

          <div className="mt-2 flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              disabled={regrade.isPending}
              onClick={() => regrade.mutate({ id: grade.id })}
            >
              {regrade.isPending ? 'Re-grading…' : 'Ask AI again'}
            </Button>
          </div>
        </div>
      )}

      {grade.status === 'reviewed' && (
        <div className="mt-3">
          <p className="text-sm font-semibold text-ink-900">
            Final grade: {grade.final_score}/{grade.max_marks}
          </p>
          {grade.suggested_score != null && grade.final_score !== grade.suggested_score && (
            <p className="mt-0.5 text-xs text-ink-400">
              AI suggested {grade.suggested_score}/{grade.max_marks} — you overrode it.
            </p>
          )}
          {grade.teacher_comment && (
            <p className="mt-1.5 text-sm text-ink-700">
              <span className="font-semibold">Your comment:</span> {grade.teacher_comment}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

// Mirrors the GradeCard layout so the list doesn't reflow when data lands.
const GradeCardSkeleton = () => (
  <div className="os-card p-4 sm:p-5">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <Skeleton w="w-1/3" h="h-5" />
        <Skeleton w="w-1/4" h="h-3" />
      </div>
      <Skeleton w="w-28" h="h-5" rounded="rounded-full" />
    </div>
    <Skeleton w="w-2/3" h="h-3" className="mt-3" />
    <Skeleton w="w-full" h="h-16" rounded="rounded-lg" className="mt-2" />
    <div className="mt-3 space-y-1.5">
      <Skeleton w="w-1/2" h="h-4" />
      <Skeleton w="w-5/6" h="h-3" />
    </div>
  </div>
);

type StatusFilter = OpenGradeStatus | 'all';

const FILTER_CHIPS: Array<{ value: StatusFilter; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'ai_graded', label: 'Needs review' },
  { value: 'pending', label: 'AI grading' },
  { value: 'reviewed', label: 'Finalised' },
  { value: 'failed', label: 'Failed' },
];

/**
 * Open-response grading queue — the first consumer of /ai/open-grades/
 * (ASA-7a). Free-text answers can't self-grade like MCQ/numeric, so the AI
 * proposes a score, feedback, and a per-criterion breakdown, and the teacher
 * reviews each one: accept in one click or override with their own marks and
 * comment. The AI never finalises anything (human firmly in the loop).
 */
export const OpenResponseGradingPage = () => {
  const navigate = useNavigate();
  const [roomFilter, setRoomFilter] = useState<number | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const { data: rooms } = useSubjectRooms();
  const {
    data: grades,
    isLoading,
    isError,
    refetch,
  } = useOpenGrades({
    subjectRoomId: roomFilter === 'all' ? undefined : roomFilter,
    status: statusFilter === 'all' ? undefined : statusFilter,
  });

  const items = grades ?? [];
  const isFiltered = roomFilter !== 'all' || statusFilter !== 'all';

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div>
        <button
          type="button"
          onClick={() => navigate('/teacher')}
          className="text-sm text-brand-700 font-medium hover:underline mb-3 inline-flex items-center gap-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        >
          ← Dashboard
        </button>
        <h1 className="font-display text-3xl font-semibold text-ink-900">AI grading</h1>
        <p className="mt-1 text-sm text-ink-500">
          Open-ended answers, graded by AI, finalised by you. Nothing counts until you review it.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <select
          aria-label="Filter by class"
          value={roomFilter === 'all' ? 'all' : String(roomFilter)}
          onChange={(e) =>
            setRoomFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))
          }
          className="input-brand w-auto text-sm"
        >
          <option value="all">All my classes</option>
          {(rooms ?? []).map((r) => (
            <option key={r.id} value={r.id}>
              {r.subject_name} · {r.classroom_display}
            </option>
          ))}
        </select>
        <div className="flex flex-wrap gap-1.5">
          {FILTER_CHIPS.map((chip) => (
            <button
              key={chip.value}
              type="button"
              onClick={() => setStatusFilter(chip.value)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === chip.value
                  ? 'bg-brand-600 text-white shadow-soft'
                  : 'bg-ink-50 text-ink-700 hover:bg-ink-100'
              }`}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="space-y-4">
          <GradeCardSkeleton />
          <GradeCardSkeleton />
        </div>
      )}

      {/* A failed fetch must not masquerade as "queue is clear" — that would
          tell the teacher there is nothing to review when we just couldn't
          reach the server. */}
      {!isLoading && isError && (
        <p className="text-sm text-rose-600">
          Couldn&apos;t load the grading queue just now.{' '}
          <button
            type="button"
            onClick={() => void refetch()}
            className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
          >
            Retry
          </button>
        </p>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <EmptyState
          title={isFiltered ? 'Nothing matches these filters' : 'No responses to grade yet'}
          description={
            isFiltered
              ? 'Try a different class or status.'
              : 'Record a student’s open-ended answer and AI will suggest a grade for your review.'
          }
        />
      )}

      {!isLoading && !isError && (
        <div className="space-y-4">
          {items.map((g) => (
            <GradeCard key={g.id} grade={g} />
          ))}
        </div>
      )}
    </div>
  );
};
