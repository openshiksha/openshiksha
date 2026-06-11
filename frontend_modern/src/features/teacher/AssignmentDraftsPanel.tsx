import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Skeleton } from '@/shared/ui';
import {
  errorDetail,
  useAssignmentDrafts,
  useApproveAssignmentDraft,
  useDismissAssignmentDraft,
  useGenerateAssignmentDraft,
  type AssignmentDraft,
} from './useAssignmentDrafts';

const pct = (v: number): string => `${Math.round(v * 100)}%`;

/** Default due date for an approved draft: a week out, as a date-input value. */
const defaultDueDate = (): string => {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  return d.toISOString().slice(0, 10);
};

interface ApproveFormProps {
  draft: AssignmentDraft;
  subjectRoomId: number;
  onCancel: () => void;
}

const ApproveForm = ({ draft, subjectRoomId, onCancel }: ApproveFormProps) => {
  const approve = useApproveAssignmentDraft(subjectRoomId);
  const [dueDate, setDueDate] = useState(defaultDueDate());
  const [title, setTitle] = useState('');

  const conflictDetail = approve.isError ? errorDetail(approve.error) : null;

  return (
    <form
      className="mt-3 rounded-lg border border-ink-100 bg-ink-50/60 p-3 space-y-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (!dueDate) return;
        approve.mutate({
          id: draft.id,
          due_at: new Date(dueDate).toISOString(),
          title: title.trim() || undefined,
        });
      }}
    >
      <label className="block text-xs text-ink-600">
        Due date
        <input
          type="date"
          required
          value={dueDate}
          min={new Date().toISOString().slice(0, 10)}
          onChange={(e) => setDueDate(e.target.value)}
          className="input-brand mt-1 block w-full max-w-[12rem] text-sm"
        />
      </label>
      <label className="block text-xs text-ink-600">
        Title <span className="text-ink-400">(optional — keeps the draft's title if blank)</span>
        <input
          type="text"
          value={title}
          maxLength={255}
          placeholder={draft.title || 'Practice set'}
          onChange={(e) => setTitle(e.target.value)}
          className="input-brand mt-1 block w-full text-sm"
        />
      </label>

      {approve.isError && (
        <p className="text-xs text-rose-600">
          {conflictDetail ?? "Couldn't approve the draft just now. Please try again in a moment."}
          {conflictDetail?.includes('Regenerate') && ' Use "Try again" to build a fresh draft.'}
        </p>
      )}

      <div className="flex gap-2 pt-1">
        <Button type="submit" variant="brand" size="sm" disabled={approve.isPending || !dueDate}>
          {approve.isPending ? 'Assigning…' : 'Assign to class'}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
};

interface CardProps {
  draft: AssignmentDraft;
  subjectRoomId: number;
}

const DraftCard = ({ draft, subjectRoomId }: CardProps) => {
  const dismiss = useDismissAssignmentDraft(subjectRoomId);
  const regenerate = useGenerateAssignmentDraft(subjectRoomId);
  const [approving, setApproving] = useState(false);
  // Like the sibling panels: the deterministic fallback selection is still
  // useful, but must never read as genuine AI output (provider transparency).
  const isStub = draft.model_used === 'stub';

  if (draft.status === 'pending') {
    return (
      <div className="rounded-xl border border-ink-100 bg-paper p-4">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-brand-500" aria-hidden />
          <p className="text-sm text-ink-700">
            Assembling a draft from your class&apos;s weak spots…
          </p>
        </div>
        <p className="mt-1 text-xs text-ink-400">This usually takes a few seconds.</p>
      </div>
    );
  }

  if (draft.status === 'failed') {
    return (
      <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-4">
        <p className="text-sm text-ink-700">Couldn&apos;t put this draft together.</p>
        {draft.error_detail && <p className="mt-1 text-xs text-ink-500">{draft.error_detail}</p>}
        <div className="mt-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={regenerate.isPending}
            onClick={() =>
              regenerate.mutate({
                size: draft.requested_size,
                target_difficulty: draft.target_difficulty,
              })
            }
          >
            {regenerate.isPending ? 'Retrying…' : 'Try again'}
          </Button>
        </div>
      </div>
    );
  }

  if (draft.status === 'approved') {
    return (
      <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
        <div className="flex items-start justify-between gap-3">
          <p className="font-display text-base text-ink-900 leading-tight min-w-0">
            {draft.title || 'Practice set'}
          </p>
          <Badge tone="success">Assigned</Badge>
        </div>
        {draft.approved_assignment != null && (
          <p className="mt-2 text-xs text-ink-600">
            <Link
              to={`/teacher/assignments/${draft.approved_assignment}`}
              className="font-medium text-brand-700 hover:text-brand-800 underline"
            >
              View the assignment
            </Link>{' '}
            — your class can see it now.
          </p>
        )}
      </div>
    );
  }

  // ready
  return (
    <div className="rounded-xl border border-ink-100 bg-paper p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="font-display text-base text-ink-900 leading-tight min-w-0">
          {draft.title || 'Practice set'}
        </p>
        <Badge tone={isStub ? 'neutral' : 'brand'} className="shrink-0">
          {isStub ? 'Auto-drafted' : '✨ AI-generated'}
        </Badge>
      </div>

      {draft.rationale_text && (
        <p className="mt-2 text-sm text-ink-700 leading-relaxed">{draft.rationale_text}</p>
      )}
      {isStub && (
        <p className="mt-1 text-xs text-ink-400">
          AI was unavailable, so this draft was built directly from your class&apos;s practice data.
        </p>
      )}

      {draft.target_chapters.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {draft.target_chapters.map((c) => (
            <span
              key={c.chapter_id}
              className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-xs text-ink-700"
            >
              {c.chapter_name}
              <span className="text-ink-400">{pct(c.avg_score)}</span>
            </span>
          ))}
        </div>
      )}

      <p className="mt-2 text-xs text-ink-500">
        {draft.question_count} question{draft.question_count !== 1 ? 's' : ''}
        {draft.estimated_minutes > 0 && ` · ~${draft.estimated_minutes} min`}
      </p>

      {dismiss.isError && (
        <p className="mt-2 text-xs text-rose-600">
          Couldn&apos;t dismiss the draft just now. Please try again in a moment.
        </p>
      )}

      {approving ? (
        <ApproveForm draft={draft} subjectRoomId={subjectRoomId} onCancel={() => setApproving(false)} />
      ) : (
        <div className="mt-3 flex items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={dismiss.isPending}
            onClick={() => dismiss.mutate({ id: draft.id })}
          >
            Dismiss
          </Button>
          <Button variant="brand" size="sm" onClick={() => setApproving(true)}>
            Approve…
          </Button>
        </div>
      )}
    </div>
  );
};

// Mirrors the ready DraftCard layout so the list doesn't reflow when data lands.
const DraftCardSkeleton = () => (
  <div className="rounded-xl border border-ink-100 bg-paper p-4">
    <div className="flex items-start justify-between gap-3">
      <Skeleton w="w-1/2" h="h-5" />
      <Skeleton w="w-24" h="h-5" rounded="rounded-full" />
    </div>
    <div className="mt-3 space-y-1.5">
      <Skeleton w="w-full" h="h-3" />
      <Skeleton w="w-5/6" h="h-3" />
    </div>
    <div className="mt-3 flex gap-1.5">
      <Skeleton w="w-24" h="h-5" rounded="rounded-full" />
      <Skeleton w="w-20" h="h-5" rounded="rounded-full" />
    </div>
  </div>
);

interface Props {
  subjectRoomId: number;
}

/**
 * AI assignment drafts — the first consumer of /ai/assignment-drafts/ (ASA-6).
 * One click takes a teacher from "my class is weak on X" to a reviewable
 * draft (selection + rationale) and, on approval, to a real ProblemSet +
 * Assignment. The teacher always has final say: approve with a due date, or
 * dismiss. Collapsed by default like its sibling insight panels; data only
 * loads when a teacher opens it.
 */
export const AssignmentDraftsPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    data: drafts,
    isLoading,
    isError,
    refetch,
  } = useAssignmentDrafts(subjectRoomId, isExpanded);
  const generate = useGenerateAssignmentDraft(subjectRoomId);
  const [size, setSize] = useState(8);
  const [difficulty, setDifficulty] = useState(2);

  // Dismissed drafts stay queryable server-side but add only noise here.
  const visible = (drafts ?? []).filter((d) => d.status !== 'dismissed');
  const actionable = visible.filter((d) => d.status === 'ready' || d.status === 'pending');

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        aria-expanded={isExpanded}
        className="flex items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-ink-800 transition-colors w-full text-left"
      >
        <span>AI Assignment Drafts</span>
        {actionable.length > 0 && <Badge tone="brand">{actionable.length}</Badge>}
        <span className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {isLoading && (
            <>
              <DraftCardSkeleton />
              <DraftCardSkeleton />
            </>
          )}

          {/* A failed fetch must not masquerade as "no drafts yet" — that would
              invite the teacher to generate a duplicate of a draft that may
              already be waiting for review. */}
          {!isLoading && isError && (
            <p className="text-xs text-rose-600 py-2">
              Couldn&apos;t load drafts just now.{' '}
              <button
                type="button"
                onClick={() => void refetch()}
                className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
              >
                Retry
              </button>
            </p>
          )}

          {!isLoading && !isError && visible.length === 0 && (
            <div className="text-xs text-ink-500 py-2">
              No drafts yet — let AI assemble a practice set from this class&apos;s weakest
              chapters, then review and assign it.
            </div>
          )}

          {!isLoading &&
            !isError &&
            visible.map((d) => <DraftCard key={d.id} draft={d} subjectRoomId={subjectRoomId} />)}

          {generate.isError && (
            <p className="text-xs text-rose-600 pt-1">
              Couldn&apos;t start a draft just now. Please try again in a moment.
            </p>
          )}

          <div className="flex flex-wrap items-end justify-between gap-2 pt-1">
            <div className="flex items-end gap-2">
              <label className="block text-xs text-ink-500">
                Questions
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={size}
                  onChange={(e) => setSize(Math.min(20, Math.max(1, Number(e.target.value) || 1)))}
                  className="input-brand mt-1 block w-16 text-sm"
                />
              </label>
              <label className="block text-xs text-ink-500">
                Difficulty
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(Number(e.target.value))}
                  className="input-brand mt-1 block w-20 text-sm"
                >
                  {[1, 2, 3, 4, 5].map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <Button
              variant="ghost"
              size="sm"
              disabled={generate.isPending}
              onClick={() => generate.mutate({ size, target_difficulty: difficulty })}
            >
              {generate.isPending ? 'Starting…' : 'Draft an assignment'}
            </Button>
          </div>
          <p className="text-xs text-ink-400">
            AI proposes, you decide — nothing reaches students until you approve it.
          </p>
        </div>
      )}
    </div>
  );
};
