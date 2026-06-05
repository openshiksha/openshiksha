import { useLearningPaths } from './useLearningPaths';
import type { LearningPath, LearningPathStep } from './useLearningPaths';
import { Badge, EmptyState, LoadingSpinner, SectionHeading } from '@/shared/ui';

const KeyholeOpen = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 16 16"
    width="12"
    height="12"
    fill="none"
    className="text-white"
  >
    <circle cx="8" cy="6" r="2" fill="currentColor" />
    <path d="M7 8 L6.5 12 L9.5 12 L9 8 Z" fill="currentColor" />
  </svg>
);

const KeyholeLocked = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 16 16"
    width="12"
    height="12"
    fill="none"
    className="text-ink-300"
  >
    <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" />
    <path
      d="M7 8 L6.5 12 L9.5 12 L9 8 Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinejoin="round"
    />
  </svg>
);

const StepRow = ({
  step,
  isCurrent,
  isLast,
}: {
  step: LearningPathStep;
  isCurrent: boolean;
  isLast: boolean;
}) => {
  const isCompleted = step.status === 'completed';
  return (
    <div className="relative">
      {!isLast && (
        <span
          aria-hidden
          className="absolute left-[11px] top-7 h-[calc(100%-0.5rem)] w-px bg-ink-100"
        />
      )}
      <div
        className={`relative flex items-start gap-3 rounded-lg px-3 py-3 transition-colors ${
          isCurrent ? 'bg-brand-50 ring-1 ring-brand-200' : ''
        }`}
      >
        <div
          className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
            isCompleted
              ? 'bg-emerald-100 text-emerald-700'
              : isCurrent
                ? 'bg-brand-600 text-white shadow-soft'
                : 'bg-ink-100 text-ink-400'
          }`}
          aria-hidden
        >
          {isCompleted ? '✓' : isCurrent ? <KeyholeOpen /> : <KeyholeLocked />}
        </div>
        <div className="min-w-0 flex-1">
          <p
            className={`text-sm font-medium ${
              isCompleted
                ? 'text-ink-400 line-through'
                : isCurrent
                  ? 'text-ink-900'
                  : 'text-ink-500'
            }`}
          >
            {step.chapter_name}
          </p>
          <p className="mt-0.5 text-xs text-ink-400">
            {step.subject_name}
            {step.is_review && (
              <span className="ml-2 text-amber-700">• Review</span>
            )}
            {isCompleted && step.score_when_completed !== null && (
              <span className="ml-2 text-emerald-700">
                {Math.round(step.score_when_completed * 100)}%
              </span>
            )}
          </p>
        </div>
        {isCurrent && (
          <Badge tone="brand" className="shrink-0">
            Up next
          </Badge>
        )}
      </div>
    </div>
  );
};

const PathCard = ({ path }: { path: LearningPath }) => {
  const progressPct = Math.round(path.progress_pct * 100);
  const sorted = [...path.steps].sort((a, b) => a.position - b.position);
  const currentIndex = (() => {
    const inProgress = sorted.findIndex((s) => s.status === 'in_progress');
    return inProgress !== -1
      ? inProgress
      : sorted.findIndex((s) => s.status === 'not_started');
  })();

  return (
    <div className="os-card p-5">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-display text-base font-semibold text-ink-900">
          {path.status_display}
        </h3>
        <span className="text-xs text-ink-500">
          {path.completed_steps} / {path.total_steps} steps
        </span>
      </div>
      <div
        className="mb-4 h-2 overflow-hidden rounded-full bg-ink-100"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progressPct}
      >
        <div
          className="h-full rounded-full bg-brand-600 transition-all"
          style={{ width: `${progressPct}%` }}
        />
      </div>
      <div>
        {sorted.map((step, i) => (
          <StepRow
            key={step.id}
            step={step}
            isCurrent={i === currentIndex}
            isLast={i === sorted.length - 1}
          />
        ))}
      </div>
    </div>
  );
};

export const LearningPathPage = () => {
  const { data: paths, isLoading } = useLearningPaths();

  if (isLoading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const activePaths = (paths ?? []).filter((p) => p.status !== 'completed');

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <SectionHeading
        as="h1"
        eyebrow="Unlock your next chapter"
        title="Your Learning Path"
        description="Steps are ordered by mastery gaps from your practice history."
        className="mb-6"
      />
      {activePaths.length === 0 ? (
        <EmptyState
          title="No learning paths yet"
          description="Complete some practice assignments to generate your path."
        />
      ) : (
        <div className="space-y-6">
          {activePaths.map((path) => (
            <PathCard key={path.id} path={path} />
          ))}
        </div>
      )}
    </div>
  );
};
