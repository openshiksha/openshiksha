import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { EmptyState, LoadingSpinner, SectionHeading } from '@/shared/ui';
import { useChildren } from './useChildren';

export const ParentInsightsLandingPage = () => {
  const { data: children, isLoading } = useChildren();
  const navigate = useNavigate();

  useEffect(() => {
    if (children && children.length === 1) {
      navigate(`/parent/insights/${children[0].id}`, { replace: true });
    }
  }, [children, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!children || children.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <SectionHeading as="h1" title="Insights" className="mb-6" />
        <EmptyState
          title="No children linked to your account"
          description="Ask the school admin to link your children's accounts."
        />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <SectionHeading
        as="h1"
        title="Insights"
        description="Choose a child to view their weekly summary."
        className="mb-6"
      />

      <div className="mt-2 grid gap-3 sm:grid-cols-2">
        {children.map((child) => (
          <Link
            key={child.id}
            to={`/parent/insights/${child.id}`}
            className="os-card p-5 hover:border-brand-300 hover:shadow-xs transition-all motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
          >
            <p className="font-display font-semibold text-ink-900">
              {child.first_name || child.username}
            </p>
            {child.grade != null && (
              <p className="text-sm text-ink-500 mt-1">Grade {child.grade}</p>
            )}
            <p className="text-sm text-brand-700 font-medium mt-3">Open insights →</p>
          </Link>
        ))}
      </div>
    </div>
  );
};
