import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, EmptyState, LoadingSpinner } from '@/shared/ui';
import { useT, useFormat } from '@/shared/i18n';
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
  const t = useT();
  const { formatDate } = useFormat();
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
    if (targetId == null) return t('psVersions.diffStart');
    if (againstId == null) return t('psVersions.diffSecond');
    return null;
  }, [rows.length, targetId, againstId, t]);

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
          title={t('psVersions.loadErrorTitle')}
          description={t('psVersions.loadErrorDesc')}
          action={<Button onClick={() => navigate('/teacher')}>{t('psVersions.backToDashboard')}</Button>}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900">{t('psVersions.title')}</h1>
          <p className="mt-1 text-sm text-ink-500">
            {t('psVersions.description')}
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate(setId != null ? `/teacher/problem-sets/${setId}/preview` : '/teacher')}
          className="text-sm font-medium text-brand-700 hover:text-brand-900"
        >
          {t('psVersions.backToPreview')}
        </button>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title={t('psVersions.emptyTitle')}
          description={t('psVersions.emptyDesc')}
        />
      ) : (
        <ul data-testid="version-list" className="overflow-hidden rounded-xl border border-ink-100 bg-paper">
          {rows.map((v) => {
            const state = stateForRow(v.id);
            return (
              <li key={v.id} className="border-b border-ink-100 last:border-b-0">
                {/* Native <button> for built-in keyboard/focus semantics; the
                    row content is all non-interactive text. */}
                <button
                  type="button"
                  data-testid={`version-row-${v.id}`}
                  data-state={state}
                  onClick={() => handleRowClick(v)}
                  className={`flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-left transition-colors ${
                    state === 'target'
                      ? 'bg-brand-50'
                      : state === 'against'
                        ? 'bg-amber-50'
                        : 'hover:bg-ink-50'
                  }`}
                >
                  <span className="block">
                    <span className="block text-sm font-semibold text-ink-900">
                      {t('psVersions.version', { number: v.version_number })}
                      {state === 'target' && (
                        <span className="ml-2 rounded bg-brand-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-brand-900">
                          {t('psVersions.target')}
                        </span>
                      )}
                      {state === 'against' && (
                        <span className="ml-2 rounded bg-amber-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-900">
                          {t('psVersions.against')}
                        </span>
                      )}
                    </span>
                    <span className="mt-0.5 block text-xs text-ink-500">
                      {formatDate(v.created_at, {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                      {v.created_by_name && <> · {v.created_by_name}</>}
                    </span>
                  </span>
                  <span className="block text-right text-xs text-ink-500">
                    <span className="block">
                      {t(
                        v.question_count === 1
                          ? 'psVersions.questionsCountOne'
                          : 'psVersions.questionsCountMany',
                        { count: v.question_count },
                      )}
                    </span>
                    <span
                      className={`mt-0.5 block ${v.assignment_count > 0 ? 'font-semibold text-ink-700' : ''}`}
                    >
                      {t(
                        v.assignment_count === 1 ? 'psVersions.pinnedOne' : 'psVersions.pinnedMany',
                        { count: v.assignment_count },
                      )}
                    </span>
                  </span>
                </button>
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
  const t = useT();
  return (
    <section
      data-testid="diff-panel"
      className="overflow-hidden rounded-xl border border-ink-100 bg-paper"
    >
      <header className="flex items-center justify-between border-b border-ink-100 px-4 py-3">
        <h2 className="font-display text-base font-semibold text-ink-900">{t('psVersions.diff')}</h2>
        <button
          type="button"
          onClick={onClear}
          className="text-xs text-ink-500 hover:text-ink-800"
        >
          {t('psVersions.clearSelection')}
        </button>
      </header>

      <div className="px-4 py-4">
        {state === 'loading' && <LoadingSpinner size="md" />}
        {state === 'error' && (
          <p className="text-sm text-red-700">{t('psVersions.diffLoadError')}</p>
        )}
        {state === 'ready' && data && (
          <DiffSummary data={data} />
        )}
      </div>
    </section>
  );
}

function DiffSummary({ data }: { data: NonNullable<ReturnType<typeof useVersionDiff>['data']> }) {
  const t = useT();
  const { target, against, diff } = data;
  const lines: string[] = [];
  if (diff.questions_added.length)
    lines.push(
      t(diff.questions_added.length === 1 ? 'psVersions.diffAddedOne' : 'psVersions.diffAddedMany', {
        count: diff.questions_added.length,
      }),
    );
  if (diff.questions_removed.length)
    lines.push(
      t(
        diff.questions_removed.length === 1
          ? 'psVersions.diffRemovedOne'
          : 'psVersions.diffRemovedMany',
        { count: diff.questions_removed.length },
      ),
    );
  if (diff.answer_changes.length)
    lines.push(
      t(diff.answer_changes.length === 1 ? 'psVersions.diffAnswerOne' : 'psVersions.diffAnswerMany', {
        count: diff.answer_changes.length,
      }),
    );
  if (diff.content_changes.length)
    lines.push(
      t(
        diff.content_changes.length === 1
          ? 'psVersions.diffContentOne'
          : 'psVersions.diffContentMany',
        { count: diff.content_changes.length },
      ),
    );

  const targetLabel = t('psVersions.version', { number: target.version_number });
  const againstLabel = against
    ? t('psVersions.version', { number: against.version_number })
    : t('psVersions.initialVersion');

  return (
    <div className="space-y-3 text-sm text-ink-800">
      <p>{t('psVersions.comparing', { target: targetLabel, against: againstLabel })}</p>
      {lines.length === 0 ? (
        <p data-testid="diff-no-changes" className="italic text-ink-500">
          {t('psVersions.identical')}
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
