import clsx from 'clsx';
import { HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Apply default padding. Turn off for media/edge-to-edge content. */
  padded?: boolean;
}

/** The warm V2 surface (`.os-card`). Migrated pages use this, not the legacy `.card`. */
export const Card = ({ padded = true, className, ...props }: CardProps) => (
  <div className={clsx('os-card', padded && 'p-6', className)} {...props} />
);
