import clsx from 'clsx';
import { ButtonHTMLAttributes, forwardRef } from 'react';

type Variant = 'brand' | 'ghost';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

// `.btn-brand` / `.btn-ghost` (components layer) carry the default `md` styling;
// size utilities (utilities layer) override padding/text for sm + lg.
const SIZES: Record<Size, string> = {
  sm: 'px-3.5 py-1.5 text-sm',
  md: '',
  lg: 'px-6 py-3 text-base',
};

/**
 * Primary/secondary action in the V2 brand language. `brand` is the "unlock"
 * action — aim for one per screen. See docs/initiatives/2026-design-system-v2.md.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'brand', size = 'md', className, type = 'button', ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={clsx(variant === 'brand' ? 'btn-brand' : 'btn-ghost', SIZES[size], className)}
      {...props}
    />
  ),
);

Button.displayName = 'Button';
