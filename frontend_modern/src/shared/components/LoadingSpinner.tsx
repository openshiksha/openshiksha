interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

export const LoadingSpinner = ({ size = 'md' }: LoadingSpinnerProps) => (
  <div
    className={`animate-spin rounded-full border-b-2 border-indigo-600 ${sizeClasses[size]}`}
    role="status"
    aria-label="Loading"
  />
);
