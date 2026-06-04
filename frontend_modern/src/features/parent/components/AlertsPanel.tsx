import { Badge } from '@/shared/ui';
import type { ParentAlert } from '../useParentSummary';

const SEVERITY_STYLES: Record<
  ParentAlert['severity'],
  { card: string; tone: 'urgent' | 'attention' | 'brand'; label: string }
> = {
  urgent: {
    card: 'border-rose-200 bg-rose-50',
    tone: 'urgent',
    label: 'Urgent',
  },
  attention: {
    card: 'border-amber-200 bg-amber-50',
    tone: 'attention',
    label: 'Attention',
  },
  info: {
    card: 'border-brand-200 bg-brand-50',
    tone: 'brand',
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
      <h3 className="text-sm font-semibold text-ink-700 uppercase tracking-wide">Alerts</h3>
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
                  <p className="font-semibold text-ink-900">{alert.label}</p>
                  <p className="text-sm text-ink-700 mt-1">{alert.detail}</p>
                </div>
                <Badge tone={styles.tone} className="shrink-0">
                  {styles.label}
                </Badge>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
