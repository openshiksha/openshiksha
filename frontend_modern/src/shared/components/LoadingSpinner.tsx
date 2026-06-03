interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  /** Optional descriptive label for screen readers. */
  label?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-[3px]',
};

/**
 * Branded loading spinner — a keyhole-inspired ring in `brand-600` on a soft
 * `brand-100` track. `motion-safe:animate-spin` honours `prefers-reduced-motion`
 * by rendering as a static ring.
 */
export const LoadingSpinner = ({ size = 'md', label = 'Loading' }: LoadingSpinnerProps) => (
  <div
    role="status"
    aria-label={label}
    className={`inline-block rounded-full border-brand-100 border-t-brand-600 motion-safe:animate-spin ${sizeClasses[size]}`}
  >
    <span className="sr-only">{label}</span>
  </div>
);
