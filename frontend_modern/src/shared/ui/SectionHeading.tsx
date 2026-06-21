import clsx from 'clsx';
import { createElement, HTMLAttributes, ReactNode } from 'react';

interface SectionHeadingProps extends Omit<HTMLAttributes<HTMLElement>, 'title'> {
  title: ReactNode;
  /** Small uppercase pre-title (e.g. section category). */
  eyebrow?: ReactNode;
  /** Subtle description rendered below the title. */
  description?: ReactNode;
  /** Right-aligned slot (e.g. a "View all" link). */
  action?: ReactNode;
  /** Heading element to render (semantic level). Defaults to `h2`. */
  as?: 'h1' | 'h2' | 'h3' | 'h4';
}

/**
 * Section header in the V2 brand language. `font-display` title, optional
 * eyebrow + description, and an action slot for inline links like "View all".
 */
export const SectionHeading = ({
  title,
  eyebrow,
  description,
  action,
  as = 'h2',
  className,
  ...props
}: SectionHeadingProps) => {
  const headingSize = as === 'h1' ? 'text-3xl sm:text-4xl' : as === 'h2' ? 'text-2xl' : 'text-xl';
  return (
    <div className={clsx('flex items-end justify-between gap-4', className)} {...props}>
      <div className="min-w-0">
        {eyebrow && (
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-brand-700">
            {eyebrow}
          </p>
        )}
        {createElement(
          as,
          { className: clsx('font-display font-semibold text-ink-900', headingSize) },
          title,
        )}
        {description && <p className="mt-1.5 max-w-2xl text-sm text-ink-500">{description}</p>}
      </div>
      {action && <div className="shrink-0 self-end">{action}</div>}
    </div>
  );
};
