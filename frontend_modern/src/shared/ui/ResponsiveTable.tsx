import { type ReactNode } from 'react';
import clsx from 'clsx';

export interface ResponsiveColumn<T> {
  key: string;
  header: ReactNode;
  /** cell renderer for both the desktop table and the mobile card value */
  cell: (row: T) => ReactNode;
  align?: 'left' | 'right';
  /**
   * if true, this column is the card's title row on mobile — rendered
   * prominently with no label. The first `primary` column wins.
   */
  primary?: boolean;
}

interface Props<T> {
  columns: ResponsiveColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  /** sr-only caption describing the table for assistive tech */
  caption?: ReactNode;
  'aria-label'?: string;
  className?: string;
}

/**
 * Dense data that reads as a real `<table>` on tablet/desktop (`sm:` and up) and
 * a stacked label/value card list on phones — no horizontal scroll, no clipped
 * columns. Follows the repo's `hidden sm:table` / `sm:hidden` dual-render
 * convention (see `Navbar`, `BottomNav`) rather than a JS media-query hook, so
 * there is no hydration flicker. Dependency-free; styled with the V2 `ink-*`
 * tokens.
 */
export function ResponsiveTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  className,
  'aria-label': ariaLabel,
}: Props<T>) {
  const primaryCol = columns.find((c) => c.primary);
  const secondaryCols = columns.filter((c) => c !== primaryCol);

  return (
    <>
      {/* Desktop / tablet: a real semantic table */}
      <table
        className={clsx('hidden w-full text-xs sm:table', className)}
        aria-label={ariaLabel}
      >
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="border-b border-ink-100 text-ink-500">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={clsx(
                  'pb-1.5 font-display font-semibold',
                  col.align === 'right' ? 'text-right' : 'text-left',
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="border-b border-ink-50 last:border-0">
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={clsx(
                    'py-1.5',
                    col.align === 'right' ? 'text-right' : 'text-left',
                  )}
                >
                  {col.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mobile: a stacked label/value card list */}
      <ul className={clsx('space-y-2 sm:hidden', className)} aria-label={ariaLabel}>
        {rows.map((row) => (
          <li
            key={rowKey(row)}
            className="rounded-lg border border-ink-100 bg-paper px-3 py-2.5"
          >
            {primaryCol && (
              <div className="mb-1.5 font-display text-sm font-semibold text-ink-800">
                {primaryCol.cell(row)}
              </div>
            )}
            <dl className="space-y-1 text-xs">
              {secondaryCols.map((col) => (
                <div key={col.key} className="flex items-center justify-between gap-3">
                  <dt className="text-ink-500">{col.header}</dt>
                  <dd className="text-right text-ink-700">{col.cell(row)}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
    </>
  );
}
