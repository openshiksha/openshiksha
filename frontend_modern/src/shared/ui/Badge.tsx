import clsx from 'clsx';
import { HTMLAttributes } from 'react';

/** Tones map to the product's alert semantics (see parent-insights AlertsPanel). */
type Tone = 'brand' | 'neutral' | 'success' | 'attention' | 'urgent';

const TONES: Record<Tone, string> = {
  brand: 'bg-brand-100 text-brand-800',
  neutral: 'bg-ink-100 text-ink-700',
  success: 'bg-emerald-100 text-emerald-800',
  attention: 'bg-amber-100 text-amber-800',
  urgent: 'bg-rose-100 text-rose-800',
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export const Badge = ({ tone = 'neutral', className, ...props }: BadgeProps) => (
  <span
    className={clsx(
      'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold',
      TONES[tone],
      className,
    )}
    {...props}
  />
);
