import { useState } from 'react';
import { Badge, Button } from '@/shared/ui';
import {
  useCalibrationSummary,
  useFlaggedCalibrations,
  useRefreshCalibrations,
  type CalibrationFlag,
  type DifficultyCalibration,
} from './useDifficultyCalibration';

const FLAG_TONE: Record<CalibrationFlag, 'urgent' | 'attention' | 'neutral' | 'success'> = {
  too_hard: 'urgent',
  low_discrimination: 'urgent',
  mislabeled: 'attention',
  too_easy: 'neutral',
  ok: 'success',
};

// Short, teacher-friendly gloss for each flag — why it surfaced and what to check.
const FLAG_HINT: Record<CalibrationFlag, string> = {
  too_hard: 'Almost no one got this right — check the wording or the keyed answer.',
  too_easy: 'Almost everyone got this right — it adds little to the set.',
  mislabeled: 'Behaves harder or easier than its authored difficulty label.',
  low_discrimination:
    'Stronger students did no better than weaker ones — often a mis-keyed answer.',
  ok: 'Behaves as authored.',
};

const pct = (v: number): string => `${Math.round(v * 100)}%`;

interface CardProps {
  item: DifficultyCalibration;
}

const CalibrationCard = ({ item }: CardProps) => {
  const delta = item.difficulty_delta;
  return (
    <div className="rounded-xl border border-ink-100 bg-paper p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-base text-ink-900 leading-tight truncate">
            {item.question_preview || `Question #${item.question_id}`}
          </p>
          <p className="text-xs text-ink-500 mt-0.5">
            {item.chapter_name} · {item.sample_size} student
            {item.sample_size !== 1 ? 's' : ''} · {pct(item.facility_index)} correct
          </p>
        </div>
        <Badge tone={FLAG_TONE[item.flag]}>{item.flag_display}</Badge>
      </div>

      <p className="mt-3 text-sm text-ink-700 leading-relaxed">{FLAG_HINT[item.flag]}</p>

      <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
        <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
          Authored difficulty <span className="text-ink-400">{item.declared_difficulty}/5</span>
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
          Observed difficulty <span className="text-ink-400">{item.empirical_difficulty}/5</span>
        </span>
        {delta !== 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
            {delta > 0 ? 'Harder' : 'Easier'} than labelled
            <span className="text-ink-400">
              {delta > 0 ? '+' : ''}
              {delta}
            </span>
          </span>
        )}
        {item.discrimination_index !== null && (
          <span className="inline-flex items-center gap-1 rounded-full bg-ink-100 px-2.5 py-0.5 text-ink-700">
            Discrimination
            <span className="text-ink-400">{item.discrimination_index.toFixed(2)}</span>
          </span>
        )}
      </div>
    </div>
  );
};

interface Props {
  subjectRoomId: number;
}

/**
 * Teacher AI Assistant — empirical question-quality (item analysis) panel.
 *
 * Surfaces questions whose real classroom performance disagrees with how they
 * were authored: too easy/hard, mis-labelled difficulty, or low discrimination
 * (a mis-keyed-answer smell). Derived purely from grading data — no LLM.
 * Collapsible to keep the dashboard tidy; only the room's teacher sees data.
 * Built on the V2 "Chalk & Unlock" primitives.
 */
export const QuestionQualityPanel = ({ subjectRoomId }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data: flagged, isLoading } = useFlaggedCalibrations(subjectRoomId, isExpanded);
  const { data: summary } = useCalibrationSummary(subjectRoomId, isExpanded);
  const refresh = useRefreshCalibrations(subjectRoomId);

  const items = flagged ?? [];

  return (
    <div className="mt-3 border-t border-ink-100 pt-3">
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-ink-800 transition-colors w-full text-left"
      >
        <span>Question Quality</span>
        {items.length > 0 && <Badge tone="attention">{items.length}</Badge>}
        <span className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {summary && summary.total_calibrated > 0 && (
            <p className="text-xs text-ink-500">
              {summary.flagged} of {summary.total_calibrated} calibrated question
              {summary.total_calibrated !== 1 ? 's' : ''} need a look.
            </p>
          )}

          {isLoading && <p className="text-xs text-ink-400 py-2">Loading question analysis…</p>}

          {!isLoading && items.length === 0 && (
            <div className="text-xs text-ink-500 py-2">
              No questions flagged yet. Calibration needs a handful of student attempts per
              question — refresh once your class has practised.
            </div>
          )}

          {!isLoading && items.map((item) => <CalibrationCard key={item.id} item={item} />)}

          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-ink-400">
              Verdicts come from how your class actually answered — no AI guesswork.
            </p>
            <Button
              variant="ghost"
              size="sm"
              disabled={refresh.isPending}
              onClick={() => refresh.mutate()}
            >
              {refresh.isPending ? 'Refreshing…' : items.length > 0 ? 'Refresh' : 'Calibrate'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
