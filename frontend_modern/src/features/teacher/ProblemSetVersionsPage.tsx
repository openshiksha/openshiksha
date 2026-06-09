import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, EmptyState, LoadingSpinner } from '@/shared/ui';
import {
  useProblemSetVersions,
  useVersionDiff,
  type VersionSummary,
} from './useProblemSetVersions';

/**
 * AIV-8: version history + diff view for a problem set.
 *
 * Lists every immutable `ProblemSetVersion` mint, newest first, with the
 * number of assignments pinned to each. Click a row to make it the **target**
 * of a diff; click a second row to make it the **against** side. The diff
 * panel renders the structured output of ``diff_snapshots`` server-side, so
 * the UI just summarises counts.
 */
export const ProblemSetVersionsPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const setId = id ? Number(id) : null;
  const versions = useProblemSetVersions(setId);
  const [targetId, setTargetId] = useState<number | null>(null);
  const [againstId, setAgainstId] = useState<number | null>(null);
  const diff = useVersionDiff(setId, targetId, againstId);

  const rows = versions.data?.versions ?? [];

  const handleRowClick = (v: VersionSummary) => {
    if (targetId == null || targetId === v.id) {
      setTargetId(v.id);
      setAgainstId(null);
      return;
    }
    setAgainstId(v.id);
  };

  const stateForRow = (vId: number): 'target' | 'against' | 'idle' => {
    if (vId === targetId) return 'target';
    if (vId === againstId) return 'against';
    return 'idle';
  };

  const helperText = useMemo(() => {
    if (rows.length === 0) return null;
    if (targetId == null) return 'Click a version to start a diff.';
    if (againstId == null) return 'Click another version to compare against.';
    return null;
  }, [rows.length, targetId, againstId]);

  if (versions.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (versions.isError || !versions.data) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <EmptyState
          title="Couldn't load version history"
          description="The set may have been removed, or you may not have access."
          action={<Button onClick={() => navigate('/teacher')}>Back to dashboard</Button>}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900">Version history</h1>
          <p className="mt-1 text-sm text-ink-500">
            Every published content version for this problem set. Newer assignments pin newer
            versions; existing assignments stay on the version they were given.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate(setId != null ? `/teacher/problem-sets/${setId}/preview` : '/teacher')}
          className="text-sm font-medium text-brand-700 hover:text-brand-900"
        >
          ← Back to preview
        </button>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title="No versions yet"
          description="A version is minted the first time this set is assigned or re-synced."
        />
      ) : (
        <ul data-testid="version-list" className="overflow-hidden rounded-xl border border-ink-100 bg-paper">
          {rows.map((v) => {
            const state = stateForRow(v.id);
            return (
              <li
                key={v.id}
                data-testid={`version-row-${v.id}`}
                data-state={state}
                className={`flex cursor-pointer items-center justify-between gap-3 border-b border-ink-100 px-4 py-3 last:border-b-0 transition-colors ${
                  state === 'target'
                    ? 'bg-brand-50'
                    : state === 'against'
                      ? 'bg-amber-50'
                      : 'hover:bg-ink-50'
                }`}
                onClick={() => handleRowClick(v)}
              >
                <div>
                  <p className="text-sm font-semibold text-ink-900">
                    v{v.version_number}
                    {state === 'target' && (
                      <span className="ml-2 rounded bg-brand-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-brand-900">
                        Target
                      </span>
                    )}
                    {state === 'against' && (
                      <span className="ml-2 rounded bg-amber-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-900">
                        Against
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-ink-500">
                    {new Date(v.created_at).toLocaleString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                    {v.created_by_name && <> · {v.created_by_name}</>}
                  </p>
                </div>
                <div className="text-right text-xs text-ink-500">
                  <p>{v.question_count} question{v.question_count === 1 ? '' : 's'}</p>
                  <p
                    className={`mt-0.5 ${v.assignment_count > 0 ? 'font-semibold text-ink-700' : ''}`}
                  >
                    {v.assignment_count} pinned assignment{v.assignment_count === 1 ? '' : 's'}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {helperText && (
        <p className="text-sm italic text-ink-500" data-testid="diff-helper-text">
          {helperText}
        </p>
      )}

      {targetId != null && (
        <DiffPanel
          state={
            diff.isLoading
              ? 'loading'
              : diff.isError || !diff.data
                ? 'error'
                : 'ready'
          }
          data={diff.data}
          onClear={() => {
            setTargetId(null);
            setAgainstId(null);
          }}
        />
      )}
    </div>
  );
};

interface DiffPanelProps {
  state: 'loading' | 'error' | 'ready';
  data: ReturnType<typeof useVersionDiff>['data'];
  onClear: () => void;
}

function DiffPanel({ state, data, onClear }: DiffPanelProps) {
  return (
    <section
      data-testid="diff-panel"
      className="overflow-hidden rounded-xl border border-ink-100 bg-paper"
    >
      <header className="flex items-center justify-between border-b border-ink-100 px-4 py-3">
        <h2 className="font-display text-base font-semibold text-ink-900">Diff</h2>
        <button
          type="button"
          onClick={onClear}
          className="text-xs text-ink-500 hover:text-ink-800"
        >
          Clear selection
        </button>
      </header>

      <div className="px-4 py-4">
        {state === 'loading' && <LoadingSpinner size="md" />}
        {state === 'error' && (
          <p className="text-sm text-red-700">Couldn't load the diff. Try again.</p>
        )}
        {state === 'ready' && data && (
          <DiffSummary data={data} />
        )}
      </div>
    </section>
  );
}

function DiffSummary({ data }: { data: NonNullable<ReturnType<typeof useVersionDiff>['data']> }) {
  const { target, against, diff } = data;
  const lines: string[] = [];
  if (diff.questions_added.length) lines.push(`${diff.questions_added.length} question(s) added`);
  if (diff.questions_removed.length) lines.push(`${diff.questions_removed.length} question(s) removed`);
  if (diff.answer_changes.length) lines.push(`${diff.answer_changes.length} answer(s) changed`);
  if (diff.content_changes.length)
    lines.push(`${diff.content_changes.length} cosmetic content edit(s)`);

  return (
    <div className="space-y-3 text-sm text-ink-800">
      <p>
        Comparing <strong>v{target.version_number}</strong> against{' '}
        <strong>{against ? `v${against.version_number}` : 'nothing (initial version)'}</strong>.
      </p>
      {lines.length === 0 ? (
        <p data-testid="diff-no-changes" className="italic text-ink-500">
          Identical content.
        </p>
      ) : (
        <ul data-testid="diff-lines" className="list-disc pl-5">
          {lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
