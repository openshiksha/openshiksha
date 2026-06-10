import { useState } from 'react';
import { Badge, Button } from '@/shared/ui';
import {
  useMisconceptionClusters,
  useRefreshMisconceptionClusters,
  type MisconceptionCluster,
} from './useMisconceptionClusters';

const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

const ClusterCard = ({ cluster }: { cluster: MisconceptionCluster }) => (
  <div className="rounded-xl border border-ink-100 bg-paper p-4">
    <div className="flex items-start justify-between gap-3">
      <p className="font-display text-base text-ink-900 leading-tight min-w-0">
        {cluster.misconception_label}
      </p>
      <Badge tone={cluster.student_count >= 3 ? 'attention' : 'neutral'} className="shrink-0">
        {cluster.student_count} student{cluster.student_count !== 1 ? 's' : ''}
      </Badge>
    </div>

    {cluster.sample_diagnosis && (
      <p className="mt-2 text-sm text-ink-700 leading-relaxed">{cluster.sample_diagnosis}</p>
    )}

    {cluster.sample_remediation_tip && (
      <p className="mt-2 text-xs text-ink-600">
        <span className="font-semibold">Try in class:</span> {cluster.sample_remediation_tip}
      </p>
    )}

    <p className="mt-3 text-xs text-ink-400">
      Seen {cluster.occurrence_count} time{cluster.occurrence_count !== 1 ? 's' : ''} · last on{' '}
      {formatDate(cluster.last_seen)} · updated {formatDate(cluster.refreshed_at)}
    </p>
  </div>
);

interface Props {
  subjectRoomId: number;
}

/**
 * Class-level misconception clusters — the first consumer of
 * /ai/misconception-clusters/. Aggregates per-student misconception
 * diagnoses into patterns a teacher can address with the whole class.
 * Collapsed by default like its sibling insight panels; data only loads
 * when a teacher opens it.
 */
export const MisconceptionClustersPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data: clusters, isLoading } = useMisconceptionClusters(subjectRoomId, isExpanded);
  const refresh = useRefreshMisconceptionClusters(subjectRoomId);

  const items = clusters ?? [];

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        aria-expanded={isExpanded}
        className="flex items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-ink-800 transition-colors w-full text-left"
      >
        <span>Class Misconceptions</span>
        {items.length > 0 && <Badge tone="brand">{items.length}</Badge>}
        <span className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {isLoading && <p className="text-xs text-ink-400 py-2">Loading misconceptions…</p>}

          {!isLoading && items.length === 0 && (
            <div className="text-xs text-ink-500 py-2">
              No misconception patterns detected yet — they appear once students have a few graded
              assignments in this class.
            </div>
          )}

          {!isLoading && items.map((c) => <ClusterCard key={c.id} cluster={c} />)}

          {refresh.isError && (
            <p className="text-xs text-rose-600 pt-1">
              Couldn&apos;t refresh just now. Please try again in a moment.
            </p>
          )}

          {refresh.isSuccess && (
            <p className="text-xs text-ink-400 pt-1" role="status">
              Recomputing from recent submissions — new patterns appear here shortly.
            </p>
          )}

          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-ink-400">
              Patterns across the whole class — address them once, help everyone.
            </p>
            <Button
              variant="ghost"
              size="sm"
              disabled={refresh.isPending}
              onClick={() => refresh.mutate()}
            >
              {refresh.isPending ? 'Refreshing…' : 'Refresh'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
