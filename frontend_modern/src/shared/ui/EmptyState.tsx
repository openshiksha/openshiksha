import clsx from 'clsx';
import { HTMLAttributes, ReactNode } from 'react';

interface EmptyStateProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  title: ReactNode;
  description?: ReactNode;
  /** Optional primary action (typically a `<Button>`). */
  action?: ReactNode;
  /** Optional custom icon node; defaults to the keyhole motif. */
  icon?: ReactNode;
}

const KeyholeGlyph = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 64 64"
    width="48"
    height="48"
    fill="none"
    className="text-brand-500"
  >
    <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="2" opacity="0.25" />
    <circle cx="32" cy="26" r="7" stroke="currentColor" strokeWidth="3" />
    <path
      d="M28 31 L26 44 L38 44 L36 31"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Canonical "nothing here yet" surface. Keyhole motif on warm paper, with an
 * optional primary action. Use for empty lists, dashboards, and search results.
 */
export const EmptyState = ({
  title,
  description,
  action,
  icon,
  className,
  ...props
}: EmptyStateProps) => (
  <div
    role="status"
    className={clsx(
      'os-card flex flex-col items-center gap-3 px-6 py-10 text-center',
      className,
    )}
    {...props}
  >
    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-50">
      {icon ?? <KeyholeGlyph />}
    </div>
    <h3 className="font-display text-lg font-semibold text-ink-900">{title}</h3>
    {description && <p className="max-w-md text-sm text-ink-500">{description}</p>}
    {action && <div className="mt-2">{action}</div>}
  </div>
);
