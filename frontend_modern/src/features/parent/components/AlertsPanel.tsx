import type { ParentAlert } from '../useParentSummary';

const SEVERITY_STYLES: Record<ParentAlert['severity'], { card: string; chip: string; label: string }> = {
  urgent: {
    card: 'border-red-200 bg-red-50',
    chip: 'bg-red-100 text-red-700',
    label: 'Urgent',
  },
  attention: {
    card: 'border-amber-200 bg-amber-50',
    chip: 'bg-amber-100 text-amber-800',
    label: 'Attention',
  },
  info: {
    card: 'border-blue-200 bg-blue-50',
    chip: 'bg-blue-100 text-blue-700',
    label: 'Info',
  },
};

interface Props {
  alerts: ParentAlert[];
}

export const AlertsPanel = ({ alerts }: Props) => {
  if (!alerts || alerts.length === 0) return null;

  return (
    <section aria-label="Alerts" className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Alerts</h3>
      <div className="space-y-2">
        {alerts.map((alert, idx) => {
          const styles = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.info;
          return (
            <div
              key={`${alert.label}-${idx}`}
              data-severity={alert.severity}
              className={`rounded-xl border p-4 ${styles.card}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900">{alert.label}</p>
                  <p className="text-sm text-gray-700 mt-1">{alert.detail}</p>
                </div>
                <span
                  className={`shrink-0 text-xs font-semibold px-2 py-1 rounded-full ${styles.chip}`}
                >
                  {styles.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
