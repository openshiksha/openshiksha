import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuestionList } from './useQuestionList';
import { useSubjects } from './useSubjects';
import { useProblemSets } from './useProblemSets';
import { useAddQuestionToProblemSet } from './useAddQuestionToProblemSet';
import { previewFromQuestionText } from './previewFromQuestionText';
import { QuestionPreviewPanel } from './QuestionPreviewPanel';
import { difficultyStars, typeLabel, typeTone } from './questionPreviewMeta';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  LoadingSpinner,
  SectionHeading,
  Select,
  Skeleton,
} from '@/shared/ui';
import type { Question } from '@/types/index';

// ── Row ─────────────────────────────────────────────────────────────────────

const QuestionRow = ({
  question,
  focused,
  onFocus,
  onEdit,
}: {
  question: Question;
  focused: boolean;
  onFocus: () => void;
  onEdit: () => void;
}) => {
  const previewText = previewFromQuestionText(question.subparts[0]?.question_text);
  const visibleTags = question.tags.slice(0, 3);
  const extraTags = question.tags.length - 3;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onFocus}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onFocus();
        }
      }}
      className={[
        'group flex cursor-pointer items-start gap-3 rounded-lg p-3 transition-all',
        focused
          ? 'bg-brand-50 ring-1 ring-brand-300 shadow-soft'
          : 'ring-1 ring-transparent hover:bg-ink-50 hover:ring-ink-100',
      ].join(' ')}
    >
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-sm text-ink-800">{previewText}</p>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <Badge tone={typeTone(question.question_type)}>{typeLabel(question.question_type)}</Badge>
          <span className="text-xs tracking-wider text-amber-500" title={`Difficulty ${question.difficulty}/5`}>
            {difficultyStars(question.difficulty)}
          </span>
          <span className="text-xs text-ink-400">
            {question.subject_name ?? `Subject ${question.subject}`}
          </span>
        </div>
        {question.tags.length > 0 && (
          <div className="mt-1.5 flex flex-wrap items-center gap-1">
            {visibleTags.map((t) => (
              <span
                key={t.id}
                className="rounded-md bg-ink-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ink-600"
              >
                {t.name}
              </span>
            ))}
            {extraTags > 0 && (
              <span className="text-[10px] text-ink-400">+{extraTags}</span>
            )}
          </div>
        )}
      </div>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onEdit();
        }}
        className="mt-1 shrink-0 rounded-md px-1.5 py-0.5 text-xs font-medium text-ink-400 opacity-0 transition-opacity hover:bg-ink-100 hover:text-ink-700 group-hover:opacity-100"
      >
        Edit
      </button>
    </div>
  );
};

// ── Add-to-set sidesheet (replaces the modal) ───────────────────────────────

const AddToProblemSetSheet = ({
  question,
  onClose,
}: {
  question: Question;
  onClose: () => void;
}) => {
  const [selectedPsId, setSelectedPsId] = useState<number | null>(null);
  const { data: problemSets, isLoading } = useProblemSets(question.subject);
  const addQuestion = useAddQuestionToProblemSet();
  const [success, setSuccess] = useState(false);

  // Lock body scroll while sheet is open
  useEffect(() => {
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = original;
    };
  }, []);

  const handleAdd = () => {
    if (!selectedPsId) return;
    addQuestion.mutate(
      { problemSetId: selectedPsId, questionId: question.id },
      { onSuccess: () => setSuccess(true) },
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-ink-900/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="flex h-full w-full max-w-md flex-col bg-paper shadow-lift">
        <div className="flex items-center justify-between border-b border-ink-100 px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">
              Add to set
            </p>
            <h3 className="font-display text-lg font-semibold text-ink-900">
              Question #{question.id}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-800"
          >
            <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {success ? (
            <EmptyState
              title="Added!"
              description="The question is now in the problem set."
              action={
                <div className="flex flex-wrap justify-center gap-3">
                  <Button onClick={onClose}>Done</Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setSuccess(false);
                      setSelectedPsId(null);
                    }}
                  >
                    Add to another
                  </Button>
                </div>
              }
            />
          ) : isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-16 w-full rounded-lg" />
              <Skeleton className="h-16 w-full rounded-lg" />
            </div>
          ) : !problemSets || problemSets.length === 0 ? (
            <div className="rounded-xl border border-dashed border-ink-200 bg-white p-6 text-center">
              <p className="text-sm text-ink-600">
                No problem sets in{' '}
                <strong className="text-ink-800">
                  {question.subject_name ?? 'this subject'}
                </strong>{' '}
                yet.
              </p>
              <Button size="sm" className="mt-3" onClick={onClose}>
                Build one →
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {problemSets.map((ps) => (
                <label
                  key={ps.id}
                  className={[
                    'flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors',
                    selectedPsId === ps.id
                      ? 'border-brand-300 bg-brand-50'
                      : 'border-ink-100 bg-white hover:border-ink-200',
                  ].join(' ')}
                >
                  <input
                    type="radio"
                    name="problem_set"
                    value={ps.id}
                    checked={selectedPsId === ps.id}
                    onChange={() => setSelectedPsId(ps.id)}
                    className="mt-1 h-4 w-4 border-ink-300 text-brand-600 focus:ring-2 focus:ring-brand-500"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-ink-900">{ps.title}</p>
                    <p className="text-xs text-ink-500">{ps.chapter_name}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      <Badge tone="brand">
                        {ps.question_count} {ps.question_count === 1 ? 'question' : 'questions'}
                      </Badge>
                      {ps.estimated_minutes && (
                        <span className="text-xs text-ink-500">~{ps.estimated_minutes} min</span>
                      )}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {!success && (
          <div className="flex items-center justify-end gap-2 border-t border-ink-100 bg-white px-6 py-4">
            {addQuestion.isError && (
              <p className="mr-auto text-xs font-medium text-rose-600">
                Failed to add. Please try again.
              </p>
            )}
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleAdd} disabled={!selectedPsId || addQuestion.isPending}>
              {addQuestion.isPending && <LoadingSpinner size="sm" />}
              Add
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

// ── Page ────────────────────────────────────────────────────────────────────

export const QuestionBankPage = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState<number | ''>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<number | ''>('');
  const [focusedQuestionId, setFocusedQuestionId] = useState<number | null>(null);
  const [modalQuestion, setModalQuestion] = useState<Question | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: subjects } = useSubjects();
  const { data: questions, isLoading } = useQuestionList({
    search: debouncedSearch || undefined,
    subject: selectedSubject !== '' ? (selectedSubject as number) : undefined,
    difficulty: selectedDifficulty !== '' ? (selectedDifficulty as number) : undefined,
  });

  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(value), 300);
  };

  const hasFilters =
    !!search || selectedSubject !== '' || selectedDifficulty !== '';

  const clearFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setSelectedSubject('');
    setSelectedDifficulty('');
  };

  const focusedQuestion = useMemo(
    () => questions?.find((q) => q.id === focusedQuestionId) ?? null,
    [questions, focusedQuestionId],
  );

  // Keep a valid question focused as results change (during render — react.dev/learn/you-might-not-need-an-effect)
  if (questions) {
    if (questions.length === 0) {
      if (focusedQuestionId !== null) setFocusedQuestionId(null);
    } else if (
      focusedQuestionId === null ||
      !questions.some((q) => q.id === focusedQuestionId)
    ) {
      setFocusedQuestionId(questions[0].id);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 lg:px-6">
      {/* Header */}
      <SectionHeading
        as="h1"
        eyebrow="Authoring"
        title="Question Bank"
        description="Browse and reuse questions across your assignments. Click a question to preview exactly how students will see it."
        action={
          <Button onClick={() => navigate('/teacher/questions/new')}>+ Create Question</Button>
        }
      />

      {/* Two-pane: filters + list (left) · preview (right) */}
      <div className="grid gap-4 lg:grid-cols-12">
        {/* List column */}
        <Card className="!p-0 lg:col-span-5 xl:col-span-4">
          {/* Filter bar */}
          <div className="space-y-3 border-b border-ink-100 px-5 py-4">
            <Input
              placeholder="Search question text, subject, chapter…"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              leftIcon={
                <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="7" cy="7" r="5" />
                  <path d="M11 11l4 4" strokeLinecap="round" />
                </svg>
              }
            />
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={selectedSubject}
                onChange={(e) =>
                  setSelectedSubject(e.target.value ? Number(e.target.value) : '')
                }
              >
                <option value="">All subjects</option>
                {(subjects ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
              <Select
                value={selectedDifficulty}
                onChange={(e) =>
                  setSelectedDifficulty(e.target.value ? Number(e.target.value) : '')
                }
              >
                <option value="">Any difficulty</option>
                {[1, 2, 3, 4, 5].map((d) => (
                  <option key={d} value={d}>
                    {'★'.repeat(d)} ({d}/5)
                  </option>
                ))}
              </Select>
            </div>
            {hasFilters && (
              <button
                type="button"
                onClick={clearFilters}
                className="text-xs font-medium text-ink-500 hover:text-ink-800"
              >
                Clear filters
              </button>
            )}
          </div>

          {/* Results */}
          <div className="px-2 py-2">
            {isLoading ? (
              <div className="space-y-2 px-1">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-lg" />
                ))}
              </div>
            ) : !questions || questions.length === 0 ? (
              <div className="py-10 text-center">
                <p className="text-sm text-ink-500">No questions found</p>
                <p className="mt-1 text-xs text-ink-400">
                  {hasFilters ? 'Try adjusting filters.' : 'Author your first question.'}
                </p>
                {!hasFilters && (
                  <Button
                    size="sm"
                    className="mt-3"
                    onClick={() => navigate('/teacher/questions/new')}
                  >
                    Create a question →
                  </Button>
                )}
              </div>
            ) : (
              <>
                <p className="px-3 pt-1 pb-2 text-xs text-ink-400">
                  {questions.length} question{questions.length !== 1 ? 's' : ''}
                </p>
                <div className="max-h-[40rem] space-y-1.5 overflow-y-auto pr-1">
                  {questions.map((q) => (
                    <QuestionRow
                      key={q.id}
                      question={q}
                      focused={focusedQuestionId === q.id}
                      onFocus={() => setFocusedQuestionId(q.id)}
                      onEdit={() => navigate(`/teacher/questions/${q.id}/edit`)}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        </Card>

        {/* Preview column */}
        <div className="lg:col-span-7 xl:col-span-8">
          <QuestionPreviewPanel
            question={focusedQuestion}
            emptyTitle="Pick a question to preview"
            emptyDescription="Click any row on the left to see exactly how students will see it — full LaTeX, options, images, and all."
            footer={
              focusedQuestion ? (
                <>
                  <p className="text-xs text-ink-500">
                    Reuse this question in any of your problem sets.
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/teacher/questions/${focusedQuestion.id}/edit`)}
                    >
                      Edit
                    </Button>
                    <Button size="sm" onClick={() => setModalQuestion(focusedQuestion)}>
                      + Add to problem set
                    </Button>
                  </div>
                </>
              ) : null
            }
          />
        </div>
      </div>

      {modalQuestion && (
        <AddToProblemSetSheet
          question={modalQuestion}
          onClose={() => setModalQuestion(null)}
        />
      )}
    </div>
  );
};
