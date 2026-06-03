import { useParams, Link } from 'react-router-dom';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { useChildren } from './useChildren';
import { useLatestParentSummary, useGenerateParentSummary } from './useParentSummary';
import { NarrativeCard } from './components/NarrativeCard';
import { AlertsPanel } from './components/AlertsPanel';
import { HomeActivitiesPanel } from './components/HomeActivitiesPanel';

export const ParentInsightsPage = () => {
  const params = useParams<{ childId: string }>();
  const childId = Number(params.childId);
  const validChildId = Number.isFinite(childId) && childId > 0 ? childId : undefined;

  const { data: children } = useChildren();
  const child = children?.find((c) => c.id === validChildId);

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
  } = useLatestParentSummary(validChildId);
  const generate = useGenerateParentSummary();

  const handleGenerate = () => {
    if (!validChildId) return;
    generate.mutate(
      { child_id: validChildId, language: 'en' },
      {
        onSuccess: () => {
          // Backend queues a Celery task; in eager mode the summary is ready immediately.
          // Refetch after a short pause to pick up either case.
          setTimeout(() => refetch(), 1500);
        },
      },
    );
  };

  if (!validChildId) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 font-medium">No child selected</p>
          <Link to="/parent/insights" className="text-indigo-600 text-sm font-medium mt-2 inline-block">
            Pick a child
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <header className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <Link
            to="/parent"
            className="text-sm text-indigo-600 font-medium hover:underline"
          >
            ← Back to dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">
            {child ? `${child.first_name || child.username}'s Insights` : 'Insights'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            A weekly progress narrative, alerts, and suggested home activities.
          </p>
        </div>
      </header>

      {isLoading && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        </div>
      )}

      {!isLoading && isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5">
          <p className="font-semibold text-red-800">Couldn't load the summary</p>
          <p className="text-sm text-red-700 mt-1">
            {(error as { message?: string })?.message || 'Please try again in a moment.'}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-3 px-3 py-1.5 text-sm font-medium rounded-md bg-red-600 text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {!isLoading && !isError && !summary && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 text-center">
          <p className="font-semibold text-gray-900">No summary yet</p>
          <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">
            We haven't generated a weekly summary for this child yet. Tap below to create one now —
            it usually takes about 30 seconds.
          </p>
          <button
            onClick={handleGenerate}
            disabled={generate.isPending}
            className="mt-4 px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed transition-colors"
          >
            {generate.isPending ? 'Generating…' : "Generate this week's summary"}
          </button>
          {generate.isError && (
            <p className="text-sm text-red-600 mt-3">
              Generation failed. Please try again.
            </p>
          )}
        </div>
      )}

      {!isLoading && !isError && summary && (
        <>
          <NarrativeCard summary={summary} />
          <AlertsPanel alerts={summary.alerts} />
          <HomeActivitiesPanel activities={summary.home_activities} />

          <div className="flex justify-end">
            <button
              onClick={handleGenerate}
              disabled={generate.isPending}
              className="px-3 py-1.5 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-60 transition-colors"
            >
              {generate.isPending ? 'Regenerating…' : 'Regenerate'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};
