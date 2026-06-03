import clsx from 'clsx';
import {
  forwardRef,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
  useId,
} from 'react';

interface FieldChromeProps {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  /** Render the field at full available width (default true). */
  block?: boolean;
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement>, FieldChromeProps {
  leftIcon?: ReactNode;
}

/**
 * Text input in the V2 brand language. Composes `.input-brand` plus accessible
 * label/hint/error wiring. Forward-refs to the underlying `<input>`.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    { label, hint, error, leftIcon, block = true, className, id, type = 'text', ...props },
    ref,
  ) => {
    const reactId = useId();
    const inputId = id ?? `${reactId}-input`;
    const hintId = hint ? `${inputId}-hint` : undefined;
    const errorId = error ? `${inputId}-error` : undefined;
    const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined;
    return (
      <div className={clsx(block && 'w-full')}>
        {label && (
          <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-ink-700">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-ink-400">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            type={type}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            className={clsx(
              'input-brand',
              leftIcon && 'pl-10',
              error && 'border-rose-400 focus:border-rose-500',
              props.disabled && 'cursor-not-allowed bg-ink-50 text-ink-400',
              className,
            )}
            {...props}
          />
        </div>
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-xs text-ink-500">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="mt-1.5 text-xs font-medium text-rose-600">
            {error}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = 'Input';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement>, FieldChromeProps {}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, block = true, className, id, rows = 4, ...props }, ref) => {
    const reactId = useId();
    const fieldId = id ?? `${reactId}-textarea`;
    const hintId = hint ? `${fieldId}-hint` : undefined;
    const errorId = error ? `${fieldId}-error` : undefined;
    const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined;
    return (
      <div className={clsx(block && 'w-full')}>
        {label && (
          <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-ink-700">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={fieldId}
          rows={rows}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={clsx(
            'input-brand resize-y',
            error && 'border-rose-400 focus:border-rose-500',
            props.disabled && 'cursor-not-allowed bg-ink-50 text-ink-400',
            className,
          )}
          {...props}
        />
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-xs text-ink-500">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="mt-1.5 text-xs font-medium text-rose-600">
            {error}
          </p>
        )}
      </div>
    );
  },
);

Textarea.displayName = 'Textarea';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement>, FieldChromeProps {}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, hint, error, block = true, className, id, children, ...props }, ref) => {
    const reactId = useId();
    const fieldId = id ?? `${reactId}-select`;
    const hintId = hint ? `${fieldId}-hint` : undefined;
    const errorId = error ? `${fieldId}-error` : undefined;
    const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined;
    return (
      <div className={clsx(block && 'w-full')}>
        {label && (
          <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-ink-700">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={fieldId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={clsx(
            'input-brand appearance-none pr-10 bg-no-repeat',
            error && 'border-rose-400 focus:border-rose-500',
            props.disabled && 'cursor-not-allowed bg-ink-50 text-ink-400',
            className,
          )}
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'><path d='M1 1l5 5 5-5' stroke='%23737373' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/></svg>\")",
            backgroundPosition: 'right 0.85rem center',
          }}
          {...props}
        >
          {children}
        </select>
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-xs text-ink-500">
            {hint}
          </p>
        )}
        {error && (
          <p id={errorId} className="mt-1.5 text-xs font-medium text-rose-600">
            {error}
          </p>
        )}
      </div>
    );
  },
);

Select.displayName = 'Select';
