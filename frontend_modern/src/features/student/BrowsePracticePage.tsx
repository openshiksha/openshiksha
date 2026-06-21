import { useState, useMemo } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QuestionCard } from './QuestionCard';
import { Button, EmptyState, LoadingSpinner, SectionHeading } from '@/shared/ui';
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
      <div
        role="alert"
        className="os-card border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
      >
        Failed to load questions.{' '}
        <button
          onClick={() => navigate('/student/browse')}
          className="underline focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
        >
          Go back
        </button>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <EmptyState
        title="No questions available for this chapter yet."
        action={
          <Link to="/student/browse">
            <Button variant="ghost" size="sm">
              ← Back to browse
            </Button>
          </Link>
        }
      />
    );
  }

  if (submitted) {
    const chapterName = questions[0].chapter_name ?? 'this chapter';
    return (
      <div className="mx-auto max-w-2xl">
        <div className="os-card p-8 text-center">
          <div className="mb-4 text-4xl">🎉</div>
          <h2 className="mb-2 font-display text-xl font-semibold text-ink-900">
            Practice Complete!
          </h2>
          <p className="mb-1 text-sm text-ink-500">{chapterName}</p>
          <p className="mb-6 text-ink-700">
            You answered {answeredCount} of {totalSubparts} question
            {totalSubparts !== 1 ? 's' : ''}.
          </p>
          <div className="flex flex-col justify-center gap-3 sm:flex-row">
            <Button
              variant="ghost"
              onClick={() => {
                setAnswers({});
                setSubmitted(false);
              }}
            >
              Practice Again
            </Button>
            <Button variant="brand" onClick={() => navigate('/student/browse')}>
              Browse More Chapters
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <SectionHeading
        as="h1"
        eyebrow="Practice"
        title={questions[0].chapter_name ?? 'Chapter Practice'}
        action={
          <span className="text-sm text-ink-500">
            {answeredCount} / {totalSubparts} answered
          </span>
        }
        className="mb-4"
      />
      <div className="mb-4">
        <Link
          to="/student/browse"
          className="rounded text-sm font-medium text-brand-700 hover:text-brand-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          ← Browse
        </Link>
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
        <Button
          variant="brand"
          size="lg"
          onClick={() => setSubmitted(true)}
          disabled={answeredCount === 0}
        >
          Submit Practice
        </Button>
      </div>
    </div>
  );
};
