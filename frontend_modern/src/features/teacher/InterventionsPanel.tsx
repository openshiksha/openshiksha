import { useState } from 'react';
import { Badge, Button } from '@/shared/ui';
import {
  useGenerateInterventions,
  useInterventions,
  useSetInterventionStatus,
  type GapSeverity,
  type InterventionSuggestion,
} from './useInterventions';

const SEVERITY_TONE: Record<GapSeverity, 'urgent' | 'attention' | 'neutral'> = {
  severe: 'urgent',
  moderate: 'attention',
  mild: 'neutral',
};

const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

const pct = (v: number): string => `${Math.round(v * 100)}%`;

interface CardProps {
  item: InterventionSuggestion;
  subjectRoomId: number;
}

const SuggestionCard = ({ item, subjectRoomId }: CardProps) => {
  const setStatus = useSetInterventionStatus(subjectRoomId);
  const busy = setStatus.isPending;

  return (
    <div className="rounded-xl border border-ink-100 bg-paper p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-lg text-ink-900 leading-tight">{item.student_name}</p>
          <p className="text-xs text-ink-500 mt-0.5">
            {item.gap_count} weak chapter{item.gap_count !== 1 ? 's' : ''} · {pct(item.avg_score)} avg
          </p>
        </div>
        <Badge tone={SEVERITY_TONE[item.severity]}>Priority {item.priority}</Badge>
      </div>

      <p className="mt-3 text-sm text-ink-700 leading-relaxed">{item.strategy_text}</p>

      {item.focus_chapters.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {item.focus_chapters.map((c) => (
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

      {item.misconception_labels.length > 0 && (
        <p className="mt-2 text-xs text-ink-600">
          <span className="font-semibold">Recurring misconception:</span>{' '}
          {item.misconception_labels.map((m) => m.label).join('; ')}
        </p>
      )}

      <div className="mt-3 flex items-center justify-between gap-2">
        <p className="text-xs text-ink-400">
          {formatDate(item.generated_at)} · {item.model_used}
        </p>
        {item.status === 'open' ? (
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              disabled={busy}
              onClick={() => setStatus.mutate({ id: item.id, status: 'dismissed' })}
            >
              Dismiss
            </Button>
            <Button
              variant="brand"
              size="sm"
              disabled={busy}
              onClick={() => setStatus.mutate({ id: item.id, status: 'acknowledged' })}
            >
              Mark as planned
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Badge tone={item.status === 'acknowledged' ? 'success' : 'neutral'}>
              {item.status === 'acknowledged' ? 'Planned' : 'Dismissed'}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              disabled={busy}
              onClick={() => setStatus.mutate({ id: item.id, status: 'resolved' })}
            >
              Resolve
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

interface Props {
  subjectRoomId: number;
}

/**
 * Teacher AI Assistant — per-student intervention strategies for struggling
 * students. Collapsible to keep the dashboard tidy; only the teacher who owns
 * the room ever sees data here. Built on the V2 "Chalk & Unlock" primitives.
 */
export const InterventionsPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data: suggestions, isLoading } = useInterventions(subjectRoomId, isExpanded);
  const generate = useGenerateInterventions(subjectRoomId);

  // Open suggestions sort first (already priority-ordered from the API).
  const active = (suggestions ?? []).filter((s) => s.status !== 'resolved');

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-ink-800 transition-colors w-full text-left"
      >
        <span>Intervention Suggestions</span>
        {active.length > 0 && <Badge tone="brand">{active.length}</Badge>}
        <span className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {isLoading && <p className="text-xs text-ink-400 py-2">Loading suggestions…</p>}

          {!isLoading && active.length === 0 && (
            <div className="text-xs text-ink-500 py-2">
              No struggling students flagged yet. Generate suggestions from current learning-gap data.
            </div>
          )}

          {!isLoading &&
            active.map((item) => (
              <SuggestionCard key={item.id} item={item} subjectRoomId={subjectRoomId} />
            ))}

          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-ink-400">AI strategies guide your follow-up — you stay in control.</p>
            <Button
              variant="ghost"
              size="sm"
              disabled={generate.isPending}
              onClick={() => generate.mutate()}
            >
              {generate.isPending ? 'Generating…' : active.length > 0 ? 'Refresh' : 'Generate'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
