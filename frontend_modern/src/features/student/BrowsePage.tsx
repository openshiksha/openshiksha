import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { useBrowseChapters } from './useBrowseChapters';
import { useSubjects } from '../teacher/useSubjects';

export const BrowsePage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [selectedStandard, setSelectedStandard] = useState<string>('');

  const { data: subjects } = useSubjects();
  const { data: chapters, isLoading, isError } = useBrowseChapters(
    selectedSubject || undefined,
    selectedStandard || undefined,
  );

  const greeting = user?.first_name ? `Hi, ${user.first_name}!` : 'Browse Subjects';

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{greeting}</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Practice from the shared question bank — choose a chapter to start.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Subjects</option>
          {subjects?.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        <select
          value={selectedStandard}
          onChange={(e) => setSelectedStandard(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-300 bg-white text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Standards</option>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>Grade {n}</option>
          ))}
        </select>
      </div>

      {/* Chapter list */}
      {isLoading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {isError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          Failed to load chapters. Please refresh the page.
        </div>
      )}

      {chapters && chapters.length === 0 && !isLoading && (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
          <p className="font-medium">No chapters found</p>
          <p className="text-sm mt-1">Try a different subject or standard filter.</p>
        </div>
      )}

      {chapters && chapters.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-700">Chapter</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700 hidden sm:table-cell">Subject</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700 hidden sm:table-cell">Grade</th>
                <th className="text-right px-4 py-3 font-medium text-gray-700">Questions</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {chapters.map((ch) => (
                <tr key={ch.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{ch.name}</td>
                  <td className="px-4 py-3 text-gray-500 hidden sm:table-cell">{ch.subject}</td>
                  <td className="px-4 py-3 text-gray-500 hidden sm:table-cell">Grade {ch.standard}</td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
                      {ch.question_count} Q
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => navigate(`/student/browse/chapter/${ch.id}`)}
                      className="text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
                    >
                      Practice →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
