import clsx from 'clsx';

interface LogoProps {
  /** `full` shows the Fraunces wordmark; `mark` is the keyhole disc only. */
  variant?: 'full' | 'mark';
  size?: 'sm' | 'md' | 'lg';
  /** Wordmark colour token class — override to `text-white` on chalkboard. */
  wordmarkClassName?: string;
  /** Gentle float — hero marks only. */
  float?: boolean;
  /** Hide the wordmark below the `sm` breakpoint (icon-only brand on phones). */
  hideWordmarkOnMobile?: boolean;
  className?: string;
}

const SIZES = {
  sm: { img: 'h-7 w-7', text: 'text-base' },
  md: { img: 'h-9 w-9', text: 'text-xl' },
  lg: { img: 'h-14 w-14', text: 'text-3xl' },
} as const;

/**
 * The OpenShiksha brand mark — the orange graduation-cap keyhole ("unlock").
 * Asset: public/brand/logo-orange.png (migrated from the legacy app).
 */
export const Logo = ({
  variant = 'full',
  size = 'md',
  wordmarkClassName,
  float = false,
  hideWordmarkOnMobile = false,
  className,
}: LogoProps) => {
  const s = SIZES[size];
  return (
    <span className={clsx('inline-flex items-center gap-2.5', className)}>
      <img
        src="/brand/logo-orange.png"
        alt="OpenShiksha"
        width={56}
        height={56}
        draggable={false}
        className={clsx(s.img, 'select-none', float && 'animate-float')}
      />
      {variant === 'full' && (
        <span
          className={clsx(
            'font-display font-semibold tracking-tight leading-none',
            s.text,
            hideWordmarkOnMobile && 'hidden sm:inline',
            wordmarkClassName ?? 'text-ink-900',
          )}
        >
          OpenShiksha
        </span>
      )}
    </span>
  );
};
