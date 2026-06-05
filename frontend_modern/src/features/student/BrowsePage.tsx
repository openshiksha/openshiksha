import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import {
  Badge,
  Button,
  EmptyState,
  LoadingSpinner,
  SectionHeading,
  Select,
} from '@/shared/ui';
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
      <SectionHeading
        as="h1"
        eyebrow="Self-directed practice"
        title={greeting}
        description="Practice from the shared question bank — choose a chapter to start."
        className="mb-6"
      />

      <div className="os-card mb-6 flex flex-wrap items-end gap-3 p-4">
        <Select
          label="Subject"
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="min-w-[12rem]"
          block={false}
        >
          <option value="">All Subjects</option>
          {subjects?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select
          label="Grade"
          value={selectedStandard}
          onChange={(e) => setSelectedStandard(e.target.value)}
          className="min-w-[10rem]"
          block={false}
        >
          <option value="">All Standards</option>
          {Array.from({ length: 12 }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>
              Grade {n}
            </option>
          ))}
        </Select>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {isError && (
        <div
          role="alert"
          className="os-card border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          Failed to load chapters. Please refresh the page.
        </div>
      )}

      {chapters && chapters.length === 0 && !isLoading && (
        <EmptyState
          title="No chapters found"
          description="Try a different subject or standard filter."
        />
      )}

      {chapters && chapters.length > 0 && (
        <div className="os-card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-100 bg-ink-50">
                <th className="px-4 py-3 text-left font-display font-semibold text-ink-700">
                  Chapter
                </th>
                <th className="hidden px-4 py-3 text-left font-display font-semibold text-ink-700 sm:table-cell">
                  Subject
                </th>
                <th className="hidden px-4 py-3 text-left font-display font-semibold text-ink-700 sm:table-cell">
                  Grade
                </th>
                <th className="px-4 py-3 text-right font-display font-semibold text-ink-700">
                  Questions
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {chapters.map((ch) => (
                <tr
                  key={ch.id}
                  className="transition-colors hover:bg-brand-50/40"
                >
                  <td className="px-4 py-3 font-medium text-ink-900">{ch.name}</td>
                  <td className="hidden px-4 py-3 text-ink-500 sm:table-cell">
                    {ch.subject}
                  </td>
                  <td className="hidden px-4 py-3 text-ink-500 sm:table-cell">
                    Grade {ch.standard}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Badge tone="brand">{ch.question_count} Q</Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="brand"
                      size="sm"
                      onClick={() => navigate(`/student/browse/chapter/${ch.id}`)}
                    >
                      Practice →
                    </Button>
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
