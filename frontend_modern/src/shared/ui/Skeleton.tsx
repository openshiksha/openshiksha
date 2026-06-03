import clsx from 'clsx';

interface SkeletonProps {
  /** Tailwind width utility (e.g. `'w-full'`, `'w-32'`). */
  w?: string;
  /** Tailwind height utility (e.g. `'h-4'`, `'h-24'`). */
  h?: string;
  /** Tailwind rounding utility — defaults to a friendly `rounded-md`. */
  rounded?: string;
  className?: string;
}

/**
 * Branded placeholder block for loading states.
 * Warm `ink-100` instead of cold gray; gentle pulse; AA-friendly contrast on paper.
 */
export const Skeleton = ({
  w = 'w-full',
  h = 'h-4',
  rounded = 'rounded-md',
  className,
}: SkeletonProps) => (
  <div
    role="status"
    aria-busy="true"
    aria-live="polite"
    className={clsx('animate-pulse bg-ink-100', w, h, rounded, className)}
  >
    <span className="sr-only">Loading…</span>
  </div>
);
