import type { HomeActivity } from '../useParentSummary';

interface Props {
  activities: HomeActivity[];
}

const isCelebrate = (a: HomeActivity) => /great|keep it up|celebrate|well done|nice work/i.test(a.title);

export const HomeActivitiesPanel = ({ activities }: Props) => {
  if (!activities || activities.length === 0) return null;

  return (
    <section aria-label="Home Activities" className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
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
                celebrate ? 'border-emerald-200 bg-emerald-50' : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-gray-900">{activity.title}</p>
                {activity.chapter_name && (
                  <span className="shrink-0 text-xs font-medium px-2 py-1 rounded-full bg-indigo-50 text-indigo-700">
                    {activity.chapter_name}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 mt-2 leading-relaxed">{activity.description}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
};
