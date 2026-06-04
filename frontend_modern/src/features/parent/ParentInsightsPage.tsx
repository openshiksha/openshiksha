import { useParams, Link } from 'react-router-dom';
import { Button, Card, EmptyState, LoadingSpinner, SectionHeading } from '@/shared/ui';
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
          setTimeout(() => refetch(), 1500);
        },
      },
    );
  };

  if (!validChildId) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <EmptyState
          title="No child selected"
          action={
            <Link
              to="/parent/insights"
              className="text-brand-700 text-sm font-medium hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
            >
              Pick a child
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <header className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <Link
            to="/parent"
            className="text-sm text-brand-700 font-medium hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
          >
            ← Back to dashboard
          </Link>
          <div className="mt-1">
            <SectionHeading
              as="h1"
              title={child ? `${child.first_name || child.username}'s Insights` : 'Insights'}
              description="A weekly progress narrative, alerts, and suggested home activities."
            />
          </div>
        </div>
      </header>

      {isLoading && (
        <Card>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
          </div>
        </Card>
      )}

      {!isLoading && isError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-5">
          <p className="font-semibold text-rose-800">Couldn't load the summary</p>
          <p className="text-sm text-rose-700 mt-1">
            {(error as { message?: string })?.message || 'Please try again in a moment.'}
          </p>
          <Button size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      {!isLoading && !isError && !summary && (
        <div>
          <EmptyState
            title="No summary yet"
            description="We haven't generated a weekly summary for this child yet. Tap below to create one now — it usually takes about 30 seconds."
            action={
              <Button onClick={handleGenerate} disabled={generate.isPending}>
                {generate.isPending ? 'Generating…' : "Generate this week's summary"}
              </Button>
            }
          />
          {generate.isError && (
            <p className="text-center text-sm text-rose-600 mt-3">Generation failed. Please try again.</p>
          )}
        </div>
      )}

      {!isLoading && !isError && summary && (
        <>
          <NarrativeCard summary={summary} />
          <AlertsPanel alerts={summary.alerts} />
          <HomeActivitiesPanel activities={summary.home_activities} />

          <div className="flex justify-end">
            <Button variant="ghost" size="sm" onClick={handleGenerate} disabled={generate.isPending}>
              {generate.isPending ? 'Regenerating…' : 'Regenerate'}
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
