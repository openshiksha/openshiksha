import { useState, useMemo } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QuestionCard } from './QuestionCard';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { PaginatedResponse, Question } from '@/types/index';

const useBrowsePractice = (chapterId: number | null) =>
  useQuery<Question[]>({
    queryKey: ['browse-practice', chapterId],
    queryFn: async () => {
      const res = await apiClient.get<PaginatedResponse<Question>>('/questions/', {
        params: { chapter: chapterId, page_size: 10 },
      });
      return res.data.results.slice(0, 10);
    },
    enabled: chapterId !== null,
  });

export const BrowsePracticePage = () => {
  const { chapterId } = useParams<{ chapterId: string }>();
  const navigate = useNavigate();
  const parsedId = chapterId ? parseInt(chapterId, 10) : null;

  const { data: questions, isLoading, isError } = useBrowsePractice(parsedId);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const totalSubparts = useMemo(
    () => questions?.reduce((sum, q) => sum + q.subparts.length, 0) ?? 0,
    [questions],
  );

  const answeredCount = useMemo(
    () => Object.values(answers).filter((v) => v && v.trim().length > 0).length,
    [answers],
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isError || !questions) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
        Failed to load questions.{' '}
        <button onClick={() => navigate('/student/browse')} className="underline">
          Go back
        </button>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <p className="font-medium">No questions available for this chapter yet.</p>
        <Link to="/student/browse" className="text-indigo-600 hover:text-indigo-800 text-sm mt-2 inline-block">
          ← Back to browse
        </Link>
      </div>
    );
  }

  if (submitted) {
    const chapterName = questions[0].chapter_name ?? 'this chapter';
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
          <div className="text-4xl mb-4">🎉</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Practice Complete!</h2>
          <p className="text-gray-500 text-sm mb-1">{chapterName}</p>
          <p className="text-gray-700 mb-6">
            You answered {answeredCount} of {totalSubparts} question{totalSubparts !== 1 ? 's' : ''}.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => {
                setAnswers({});
                setSubmitted(false);
              }}
              className="px-5 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Practice Again
            </button>
            <Link
              to="/student/browse"
              className="px-5 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors text-center"
            >
              Browse More Chapters
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <Link to="/student/browse" className="text-sm text-indigo-600 hover:text-indigo-800">
          ← Browse
        </Link>
        <span className="text-sm text-gray-500">
          {answeredCount} / {totalSubparts} answered
        </span>
      </div>

      <div className="space-y-4">
        {questions.map((question, idx) => (
          <QuestionCard
            key={question.id}
            question={question}
            questionNumber={idx + 1}
            answers={answers}
            onAnswerChange={(subpartId, value) =>
              setAnswers((prev) => ({ ...prev, [String(subpartId)]: value }))
            }
            isSubmitted={false}
          />
        ))}
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={() => setSubmitted(true)}
          disabled={answeredCount === 0}
          className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold rounded-lg transition-colors"
        >
          Submit Practice
        </button>
      </div>
    </div>
  );
};
