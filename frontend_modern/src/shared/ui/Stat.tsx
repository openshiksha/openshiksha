import clsx from 'clsx';
import { HTMLAttributes, ReactNode } from 'react';
import { Badge } from './Badge';

type Tone = 'brand' | 'neutral' | 'success' | 'attention' | 'urgent';

interface StatProps extends HTMLAttributes<HTMLDivElement> {
  label: ReactNode;
  value: ReactNode;
  /** Optional trend or delta text (e.g. "+12% this week"). */
  delta?: ReactNode;
  /** Tone for the optional delta pill. */
  tone?: Tone;
  /** Optional small caption rendered under the value (e.g. context like "of 20 due"). */
  hint?: ReactNode;
}

/**
 * Headline metric block — used for dashboard KPIs. Big display-font value over a
 * small uppercase label, with an optional trend pill.
 */
export const Stat = ({
  label,
  value,
  delta,
  tone = 'neutral',
  hint,
  className,
  ...props
}: StatProps) => (
  <div className={clsx('flex flex-col gap-1', className)} {...props}>
    <p className="text-xs font-semibold uppercase tracking-widest text-ink-400">{label}</p>
    <div className="flex items-baseline gap-3">
      <span className="font-display text-3xl font-semibold text-ink-900 sm:text-4xl">
        {value}
      </span>
      {delta && <Badge tone={tone}>{delta}</Badge>}
    </div>
    {hint && <p className="text-xs text-ink-500">{hint}</p>}
  </div>
);
