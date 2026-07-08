import { useState } from 'react';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  LoadingSpinner,
  SectionHeading,
  Textarea,
} from '@/shared/ui';
import { InteractiveWidget } from '@/shared/ui/InteractiveWidget';
import { QuestionPreviewPanel } from '@/features/teacher/QuestionPreviewPanel';
import { packQuestionToPreview } from './submissionPreview';
import {
  useContentSubmission,
  useContentSubmissions,
  useSubmissionTransition,
  type ContentSubmissionSummary,
  type SubmissionState,
} from './useContentSubmissions';

/**
 * CP-4 — the maintainer's one-click approval surface.
 *
 * Lists staged content packs (`ContentSubmission` rows imported by CP-2),
 * previews the actual questions/widgets a pack would add — the same
 * `QuestionPreviewPanel` teachers trust, plus the real sandboxed widget
 * preview — and drives approve/reject/reopen through the CP-3 API. All
 * legality lives server-side in the state machine; a 409 is shown, never
 * papered over. Nothing on this page writes to the bank directly:
 * materialization happens in the backend approve action.
 */

const STATE_FILTERS: { value: SubmissionState | 'all'; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'superseded', label: 'Superseded' },
  { value: 'all', label: 'All' },
];

const STATE_TONES: Record<SubmissionState, 'attention' | 'success' | 'urgent' | 'neutral'> = {
  pending: 'attention',
  approved: 'success',
  rejected: 'urgent',
  superseded: 'neutral',
};

const SubmissionRow = ({
  submission,
  selected,
  onSelect,
}: {
  submission: ContentSubmissionSummary;
  selected: boolean;
  onSelect: () => void;
}) => (
  <button
    type="button"
    onClick={onSelect}
    aria-pressed={selected}
    className={`w-full rounded-xl border p-4 text-left transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 ${
      selected
        ? 'border-brand-400 bg-brand-50/60'
        : 'border-ink-100 bg-white hover:border-brand-300 hover:bg-brand-50/30'
    }`}
  >
    <div className="flex items-center justify-between gap-3">
      <p className="min-w-0 truncate font-semibold text-ink-900">
        {submission.name || 'Untitled pack'}
      </p>
      <Badge tone={STATE_TONES[submission.state]}>{submission.state_display}</Badge>
    </div>
    <p className="mt-1 text-sm text-ink-500">
      {submission.provenance.author} · {submission.question_count} question
      {submission.question_count !== 1 ? 's' : ''}
    </p>
    <p className="mt-0.5 font-mono text-[11px] text-ink-400">
      {submission.pack_hash.slice(0, 16)}
    </p>
  </button>
);

const ProvenanceBlock = ({ submission }: { submission: ContentSubmissionSummary }) => (
  <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-ink-400">Author</dt>
      <dd className="text-ink-800">{submission.provenance.author}</dd>
    </div>
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-ink-400">License</dt>
      <dd className="text-ink-800">{submission.provenance.license}</dd>
    </div>
    {submission.provenance.source && (
      <div className="sm:col-span-2">
        <dt className="text-xs font-semibold uppercase tracking-wide text-ink-400">Source</dt>
        <dd className="break-all text-ink-800">{submission.provenance.source}</dd>
      </div>
    )}
    {submission.provenance.contact && (
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-ink-400">Contact</dt>
        <dd className="text-ink-800">{submission.provenance.contact}</dd>
      </div>
    )}
  </dl>
);

const extractApiError = (err: unknown): string => {
  const data = (err as { response?: { data?: { detail?: string; note?: string[] } } })?.response
    ?.data;
  return data?.detail ?? data?.note?.[0] ?? 'The action failed. Reload and try again.';
};

const SubmissionDetail = ({ id }: { id: number }) => {
  const { data: submission, isLoading } = useContentSubmission(id);
  const transition = useSubmissionTransition();
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !submission) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const act = (action: 'approve' | 'reject' | 'reopen') => {
    setError(null);
    if (action === 'reject' && !note.trim()) {
      setError('A note explaining the rejection is required.');
      return;
    }
    transition.mutate(
      { id: submission.id, action, note: note.trim() || undefined },
      {
        onSuccess: () => setNote(''),
        onError: (err) => setError(extractApiError(err)),
      },
    );
  };

  const questions = submission.payload?.questions ?? [];

  return (
    <div className="space-y-6">
      {/* Pack header + provenance — the durable attribution trail. */}
      <Card>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="font-display text-lg font-semibold text-ink-900">
            {submission.name || 'Untitled pack'}
          </h2>
          <Badge tone={STATE_TONES[submission.state]}>{submission.state_display}</Badge>
          <span className="ml-auto font-mono text-xs text-ink-400">
            {submission.pack_hash.slice(0, 16)}
          </span>
        </div>
        <div className="mt-4">
          <ProvenanceBlock submission={submission} />
        </div>
        {submission.reviewed_at && (
          <p className="mt-4 border-t border-ink-100 pt-3 text-sm text-ink-500">
            Reviewed by <span className="font-medium">{submission.reviewer_username}</span>
            {submission.note && <> — “{submission.note}”</>}
          </p>
        )}
      </Card>

      {/* Review actions — legality is the server's state machine, not ours. */}
      <Card>
        {submission.state === 'pending' ? (
          <div className="space-y-3">
            <Textarea
              label="Review note (required to reject)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Great fractions set — approved. / Answers to Q2 are wrong."
              rows={2}
            />
            {error && (
              <p className="text-sm text-rose-600" role="alert">
                {error}
              </p>
            )}
            <div className="flex flex-wrap justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => act('reject')}
                disabled={transition.isPending}
              >
                Reject
              </Button>
              <Button size="sm" onClick={() => act('approve')} disabled={transition.isPending}>
                {transition.isPending ? 'Working…' : 'Approve & publish to bank'}
              </Button>
            </div>
            <p className="text-xs text-ink-400">
              Approving materializes these questions into the shared bank with attribution.
              Nothing reaches students until you approve.
            </p>
          </div>
        ) : submission.state === 'rejected' ? (
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-ink-600">
              This pack was rejected. Reopen it to review again.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => act('reopen')}
              disabled={transition.isPending}
            >
              Reopen
            </Button>
          </div>
        ) : (
          <p className="text-sm text-ink-500">
            {submission.state === 'approved'
              ? 'This pack has been approved; its questions are live in the shared bank.'
              : 'This pack was superseded by a newer import.'}
          </p>
        )}
        {error && submission.state !== 'pending' && (
          <p className="mt-2 text-sm text-rose-600" role="alert">
            {error}
          </p>
        )}
      </Card>

      {/* The actual content — rendered with the same preview teachers use. */}
      {questions.map((q, i) => {
        const widgetSubparts = q.subparts.filter((sp) => sp.widget_kind);
        return (
          <div key={i} className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-widest text-ink-400">
              Question {i + 1} of {questions.length} · Grade {q.standard} · {q.subject} ·{' '}
              {q.chapter}
            </p>
            <QuestionPreviewPanel question={packQuestionToPreview(q, i)} />
            {widgetSubparts.map((sp) => (
              <div key={sp.index}>
                <p className="mb-1 text-xs font-medium text-violet-800">
                  Widget preview (sandboxed) — {sp.widget_kind}
                </p>
                <InteractiveWidget
                  kind={sp.widget_kind}
                  config={sp.widget_config ?? {}}
                  minHeight={320}
                />
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
};

export const SubmissionsPage = () => {
  const [stateFilter, setStateFilter] = useState<SubmissionState | 'all'>('pending');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data: submissions, isLoading } = useContentSubmissions(stateFilter);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <SectionHeading
        as="h1"
        title="Content Submissions"
        description="Community content packs staged for review. Approve to publish into the shared question bank with attribution — nothing external reaches students unreviewed."
      />

      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by state">
        {STATE_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => {
              setStateFilter(f.value);
              setSelectedId(null);
            }}
            aria-pressed={stateFilter === f.value}
            className={`rounded-full px-3 py-1 text-sm font-medium transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
              stateFilter === f.value
                ? 'bg-brand-600 text-white'
                : 'bg-ink-100 text-ink-600 hover:bg-ink-200'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(16rem,22rem)_1fr]">
        <div className="space-y-3">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : !submissions || submissions.length === 0 ? (
            <EmptyState
              title="No submissions"
              description="Imported content packs will appear here for review. Import one with manage.py import_content_pack."
            />
          ) : (
            submissions.map((s) => (
              <SubmissionRow
                key={s.id}
                submission={s}
                selected={selectedId === s.id}
                onSelect={() => setSelectedId(s.id)}
              />
            ))
          )}
        </div>

        <div>
          {selectedId === null ? (
            <Card className="flex min-h-[16rem] items-center justify-center text-center">
              <p className="max-w-sm text-sm text-ink-500">
                Select a submission to preview its questions and widgets exactly as students
                would see them.
              </p>
            </Card>
          ) : (
            <SubmissionDetail id={selectedId} />
          )}
        </div>
      </div>
    </div>
  );
};
