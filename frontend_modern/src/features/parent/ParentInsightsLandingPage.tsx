import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
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
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Insights</h1>
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 font-medium">No children linked to your account</p>
          <p className="text-sm text-gray-400 mt-1">
            Ask the school admin to link your children's accounts.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900">Insights</h1>
      <p className="text-sm text-gray-500 mt-1">Choose a child to view their weekly summary.</p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {children.map((child) => (
          <Link
            key={child.id}
            to={`/parent/insights/${child.id}`}
            className="rounded-xl border border-gray-200 bg-white p-5 hover:border-indigo-300 hover:shadow-sm transition-all"
          >
            <p className="font-semibold text-gray-900">
              {child.first_name || child.username}
            </p>
            {child.grade != null && (
              <p className="text-sm text-gray-500 mt-1">Grade {child.grade}</p>
            )}
            <p className="text-sm text-indigo-600 font-medium mt-3">Open insights →</p>
          </Link>
        ))}
      </div>
    </div>
  );
};
