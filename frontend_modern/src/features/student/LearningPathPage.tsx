import { useLearningPaths } from './useLearningPaths';
import type { LearningPath, LearningPathStep } from './useLearningPaths';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';

const StepRow = ({ step, isCurrent }: { step: LearningPathStep; isCurrent: boolean }) => {
  const isCompleted = step.status === 'completed';
  return (
    <div
      className={`flex items-start gap-3 py-3 border-b border-gray-100 last:border-0 ${
        isCurrent ? 'bg-indigo-50 -mx-4 px-4 rounded-lg' : ''
      }`}
    >
      <div
        className={`mt-0.5 shrink-0 flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
          isCompleted
            ? 'bg-green-100 text-green-700'
            : isCurrent
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-400'
        }`}
      >
        {isCompleted ? '✓' : step.position + 1}
      </div>
      <div className="min-w-0 flex-1">
        <p
          className={`text-sm font-medium ${
            isCompleted ? 'text-gray-400 line-through' : isCurrent ? 'text-gray-900' : 'text-gray-500'
          }`}
        >
          {step.chapter_name}
        </p>
        <p className="text-xs text-gray-400 mt-0.5">
          {step.subject_name}
          {step.is_review && <span className="ml-2 text-amber-600">• Review</span>}
          {isCompleted && step.score_when_completed !== null && (
            <span className="ml-2 text-green-600">
              {Math.round(step.score_when_completed * 100)}%
            </span>
          )}
        </p>
      </div>
      {isCurrent && (
        <span className="shrink-0 text-xs font-medium text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded-full">
          Up next
        </span>
      )}
    </div>
  );
};

const PathCard = ({ path }: { path: LearningPath }) => {
  const progressPct = Math.round(path.progress_pct * 100);
  const sorted = [...path.steps].sort((a, b) => a.position - b.position);
  const currentIndex = (() => {
    const inProgress = sorted.findIndex((s) => s.status === 'in_progress');
    return inProgress !== -1 ? inProgress : sorted.findIndex((s) => s.status === 'not_started');
  })();

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900">{path.status_display}</h3>
        <span className="text-xs text-gray-500">
          {path.completed_steps} / {path.total_steps} steps
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all"
          style={{ width: `${progressPct}%` }}
        />
      </div>
      <div>
        {sorted.map((step, i) => (
          <StepRow key={step.id} step={step} isCurrent={i === currentIndex} />
        ))}
      </div>
    </div>
  );
};

export const LearningPathPage = () => {
  const { data: paths, isLoading } = useLearningPaths();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const activePaths = (paths ?? []).filter((p) => p.status !== 'completed');

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Your Learning Path</h1>
        <p className="text-sm text-gray-500 mt-1">
          Steps are ordered by mastery gaps from your practice history.
        </p>
      </div>
      {activePaths.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-base font-medium">No learning paths yet</p>
          <p className="text-sm mt-1">
            Complete some practice assignments to generate your path.
          </p>
        </div>
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
