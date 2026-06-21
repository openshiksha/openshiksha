import { Badge } from '@/shared/ui';
import type { HomeActivity } from '../useParentSummary';

interface Props {
  activities: HomeActivity[];
}

const isCelebrate = (a: HomeActivity) => /great|keep it up|celebrate|well done|nice work/i.test(a.title);

export const HomeActivitiesPanel = ({ activities }: Props) => {
  if (!activities || activities.length === 0) return null;

  return (
    <section aria-label="Home Activities" className="space-y-3">
      <h3 className="text-sm font-semibold text-ink-700 uppercase tracking-wide">
        Try this week at home
      </h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {activities.map((activity, idx) => {
          const celebrate = isCelebrate(activity);
          return (
            <div
              key={`${activity.title}-${idx}`}
              data-celebrate={celebrate || undefined}
              className={`rounded-xl border p-4 ${
                celebrate ? 'border-emerald-200 bg-emerald-50' : 'os-card'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-ink-900">{activity.title}</p>
                {activity.chapter_name && (
                  <Badge tone="brand" className="shrink-0">
                    {activity.chapter_name}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-ink-700 mt-2 leading-relaxed">{activity.description}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
};
