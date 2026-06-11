import { useState } from 'react';
import { Badge, Button, Skeleton } from '@/shared/ui';
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
  // The provider cascade falls back to a deterministic, data-derived strategy when
  // no LLM key is configured. That guidance is still useful, but teachers must not
  // see it presented as genuine AI output (provider-cascade transparency).
  const isStub = item.model_used === 'stub';

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

      <div className="mt-3">
        <Badge tone={isStub ? 'neutral' : 'brand'}>
          {isStub ? 'Auto-strategy' : '✨ AI-generated'}
        </Badge>
        <p className="mt-2 text-sm text-ink-700 leading-relaxed">{item.strategy_text}</p>
        {isStub && (
          <p className="mt-1 text-xs text-ink-400">
            AI was unavailable, so this strategy was built directly from {item.student_name}'s
            learning-gap data.
          </p>
        )}
      </div>

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
          Generated {formatDate(item.generated_at)}
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

// Mirrors the SuggestionCard layout so the list doesn't reflow when data lands.
const SuggestionCardSkeleton = () => (
  <div className="rounded-xl border border-ink-100 bg-paper p-4">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0 flex-1 space-y-1.5">
        <Skeleton w="w-1/2" h="h-5" />
        <Skeleton w="w-1/3" h="h-3" />
      </div>
      <Skeleton w="w-20" h="h-5" rounded="rounded-full" />
    </div>
    <div className="mt-3 space-y-1.5">
      <Skeleton w="w-24" h="h-5" rounded="rounded-full" />
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
 * Teacher AI Assistant — per-student intervention strategies for struggling
 * students. Collapsible to keep the dashboard tidy; only the teacher who owns
 * the room ever sees data here. Built on the V2 "Chalk & Unlock" primitives.
 */
export const InterventionsPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const {
    data: suggestions,
    isLoading,
    isError,
    refetch,
  } = useInterventions(subjectRoomId, isExpanded);
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
          {isLoading && (
            <>
              <SuggestionCardSkeleton />
              <SuggestionCardSkeleton />
            </>
          )}

          {/* A failed fetch must not masquerade as "no struggling students" —
              that would tell the teacher their class is fine when we just
              couldn't reach the server. */}
          {!isLoading && isError && (
            <p className="text-xs text-rose-600 py-2">
              Couldn&apos;t load suggestions just now.{' '}
              <button
                type="button"
                onClick={() => void refetch()}
                className="font-medium underline hover:text-rose-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
              >
                Retry
              </button>
            </p>
          )}

          {!isLoading && !isError && active.length === 0 && (
            <div className="text-xs text-ink-500 py-2">
              No struggling students flagged yet. Generate suggestions from current learning-gap data.
            </div>
          )}

          {!isLoading &&
            !isError &&
            active.map((item) => (
              <SuggestionCard key={item.id} item={item} subjectRoomId={subjectRoomId} />
            ))}

          {generate.isError && (
            <p className="text-xs text-rose-600 pt-1">
              Couldn't generate suggestions just now. Please try again in a moment.
            </p>
          )}

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
