import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuestionList } from './useQuestionList';
import { useSubjects } from './useSubjects';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { Question } from '@/types/index';

const TYPE_BADGE: Record<string, string> = {
  mcq: 'bg-indigo-100 text-indigo-800',
  numeric: 'bg-green-100 text-green-800',
  fill_blank: 'bg-amber-100 text-amber-800',
  multi_select: 'bg-purple-100 text-purple-800',
  matching: 'bg-pink-100 text-pink-800',
};

const DifficultyDots = ({ difficulty }: { difficulty: number }) => (
  <span className="flex items-center gap-0.5">
    {Array.from({ length: 5 }, (_, i) => (
      <span
        key={i}
        className={`inline-block w-2 h-2 rounded-full ${i < difficulty ? 'bg-indigo-500' : 'bg-gray-200'}`}
      />
    ))}
  </span>
);

const QuestionCard = ({ question }: { question: Question }) => {
  const firstSubpart = question.subparts[0];
  const previewText = firstSubpart?.question_text ?? '—';
  const preview = previewText.slice(0, 120);
  const truncated = previewText.length > 120;
  const visibleTags = question.tags.slice(0, 3);
  const extraTags = question.tags.length - 3;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-300 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${TYPE_BADGE[question.question_type] ?? 'bg-gray-100 text-gray-700'}`}
          >
            {question.question_type_display ?? question.question_type}
          </span>
          <DifficultyDots difficulty={question.difficulty} />
        </div>
        <span className="text-xs text-gray-400 shrink-0">#{question.id}</span>
      </div>

      <p className="text-xs text-gray-500 mb-2">
        {question.subject_name ?? `Subject ${question.subject}`}
        {' · '}
        {question.chapter_name ?? `Chapter ${question.chapter}`}
      </p>

      <p className="text-xs font-mono text-gray-800 leading-relaxed mb-3 line-clamp-2">
        {preview}{truncated ? '…' : ''}
      </p>

      {question.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {visibleTags.map((t) => (
            <span key={t.id} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
              {t.name}
            </span>
          ))}
          {extraTags > 0 && (
            <span className="text-xs text-gray-400">+{extraTags} more</span>
          )}
        </div>
      )}
    </div>
  );
};

export const QuestionBankPage = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState<number | undefined>();
  const [selectedDifficulty, setSelectedDifficulty] = useState<number | undefined>();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: subjects } = useSubjects();
  const { data: questions, isLoading } = useQuestionList({
    search: debouncedSearch || undefined,
    subject: selectedSubject,
    difficulty: selectedDifficulty,
  });

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(value), 300);
  };

  const hasFilters = !!(search || selectedSubject || selectedDifficulty);

  const clearFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setSelectedSubject(undefined);
    setSelectedDifficulty(undefined);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Question Bank</h1>
          <p className="text-sm text-gray-500 mt-1">Browse and reuse questions across your assignments.</p>
        </div>
        <button
          onClick={() => navigate('/teacher/questions/new')}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shrink-0"
        >
          + Create Question
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          placeholder="Search by subject or chapter name…"
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="flex-1 min-w-48 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select
          value={selectedSubject ?? ''}
          onChange={(e) => setSelectedSubject(e.target.value ? Number(e.target.value) : undefined)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All subjects</option>
          {(subjects ?? []).map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select
          value={selectedDifficulty ?? ''}
          onChange={(e) => setSelectedDifficulty(e.target.value ? Number(e.target.value) : undefined)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All difficulties</option>
          {[1, 2, 3, 4, 5].map((d) => (
            <option key={d} value={d}>Difficulty {d}</option>
          ))}
        </select>
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 px-2 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : !questions || questions.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 font-medium">No questions found</p>
          <p className="text-sm text-gray-400 mt-1">
            {hasFilters
              ? 'Try adjusting your filters.'
              : 'Create your first question to build the bank.'}
          </p>
          {!hasFilters && (
            <button
              onClick={() => navigate('/teacher/questions/new')}
              className="mt-3 text-sm text-indigo-600 hover:underline"
            >
              Create a question →
            </button>
          )}
        </div>
      ) : (
        <>
          <p className="text-xs text-gray-400 mb-3">
            {questions.length} question{questions.length !== 1 ? 's' : ''}
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {questions.map((q) => (
              <QuestionCard key={q.id} question={q} />
            ))}
          </div>
        </>
      )}
    </div>
  );
};
