import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { useChapters } from './useChapters';
import { useQuestionList } from './useQuestionList';
import { useCreateProblemSet } from './useCreateProblemSet';
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

// ── Picker row ──────────────────────────────────────────────────────────────

const QuestionRow = ({
  question,
  selected,
  focused,
  onToggle,
  onFocus,
}: {
  question: Question;
  selected: boolean;
  focused: boolean;
  onToggle: () => void;
  onFocus: () => void;
}) => {
  const firstSubpart = question.subparts[0];
  const previewText = previewFromQuestionText(firstSubpart?.question_text);

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
          : selected
            ? 'bg-brand-50/50 ring-1 ring-brand-100 hover:ring-brand-200'
            : 'hover:bg-ink-50 ring-1 ring-transparent',
      ].join(' ')}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        onClick={(e) => e.stopPropagation()}
        aria-label={`Select question ${question.id}`}
        className="mt-1 h-4 w-4 shrink-0 rounded border-ink-300 text-brand-600 focus:ring-2 focus:ring-brand-500 focus:ring-offset-0"
      />
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-sm text-ink-800">{previewText}</p>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <Badge tone={typeTone(question.question_type)}>{typeLabel(question.question_type)}</Badge>
          <span
            className="text-xs tracking-wider text-amber-500"
            title={`Difficulty ${question.difficulty}/5`}
          >
            {difficultyStars(question.difficulty)}
          </span>
          {question.subparts.length > 1 && (
            <span className="text-xs text-ink-400">{question.subparts.length} parts</span>
          )}
          {firstSubpart?.is_interactive && (
            <Badge tone="urgent" className="!bg-violet-100 !text-violet-800">
              Interactive
            </Badge>
          )}
        </div>
      </div>
      {selected && (
        <span
          className="mt-1 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white"
          aria-label="In set"
        >
          <svg viewBox="0 0 12 12" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M2.5 6.5l2.5 2.5 4.5-5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      )}
    </div>
  );
};

// Preview pane is now the shared `<QuestionPreviewPanel>`.

// ── Selected-questions sticky strip ─────────────────────────────────────────

const SelectedStrip = ({
  selectedQuestions,
  onRemove,
}: {
  selectedQuestions: Question[];
  onRemove: (id: number) => void;
}) => {
  if (selectedQuestions.length === 0) return null;
  return (
    <Card className="!bg-brand-50/40 !ring-1 !ring-brand-100">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-2xl font-semibold text-ink-900">
            {selectedQuestions.length}
          </span>
          <span className="text-sm text-ink-600">
            {selectedQuestions.length === 1 ? 'question selected' : 'questions selected'}
          </span>
        </div>
      </div>
      <ul className="mt-3 flex flex-wrap gap-2">
        {selectedQuestions.map((q) => (
          <li
            key={q.id}
            className="group inline-flex max-w-xs items-center gap-1.5 rounded-full border border-brand-200 bg-white px-3 py-1 text-xs text-ink-700 shadow-soft"
          >
            <Badge tone={typeTone(q.question_type)} className="!px-1.5 !py-0 !text-[10px]">
              {typeLabel(q.question_type)}
            </Badge>
            <span className="truncate">
              {previewFromQuestionText(q.subparts[0]?.question_text).slice(0, 50)}
            </span>
            <button
              type="button"
              onClick={() => onRemove(q.id)}
              aria-label={`Remove question ${q.id}`}
              className="ml-1 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-ink-400 hover:bg-rose-100 hover:text-rose-700"
            >
              <svg viewBox="0 0 8 8" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 1l6 6M7 1L1 7" strokeLinecap="round" />
              </svg>
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
};

// ── Page ────────────────────────────────────────────────────────────────────

export const CreateProblemSetPage = () => {
  const navigate = useNavigate();
  const { data: subjectRooms } = useSubjectRooms();

  const [title, setTitle] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | ''>('');
  const [selectedChapterId, setSelectedChapterId] = useState<number | ''>('');
  const [estimatedMinutes, setEstimatedMinutes] = useState<string>('');
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<Set<number>>(new Set());
  const [focusedQuestionId, setFocusedQuestionId] = useState<number | null>(null);
  const [successId, setSuccessId] = useState<number | null>(null);

  // Filters within the picker
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<number | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  const { data: chapters } = useChapters(
    selectedSubjectId !== '' ? selectedSubjectId : undefined,
  );

  const { data: questions, isLoading: questionsLoading } = useQuestionList(
    selectedSubjectId !== '' && selectedChapterId !== ''
      ? { subject: selectedSubjectId as number, chapter: selectedChapterId as number }
      : selectedSubjectId !== ''
        ? { subject: selectedSubjectId as number }
        : {},
  );

  const createProblemSet = useCreateProblemSet();

  const subjects = Array.from(
    new Map(
      subjectRooms?.map((r) => [r.subject, { id: r.subject, name: r.subject_name }]) ?? [],
    ).values(),
  );

  const filteredQuestions = useMemo(() => {
    if (!questions) return [];
    const q = searchQuery.trim().toLowerCase();
    return questions.filter((qu) => {
      if (difficultyFilter !== null && qu.difficulty !== difficultyFilter) return false;
      if (typeFilter && qu.question_type !== typeFilter) return false;
      if (q) {
        const preview = previewFromQuestionText(qu.subparts[0]?.question_text).toLowerCase();
        if (!preview.includes(q)) return false;
      }
      return true;
    });
  }, [questions, searchQuery, difficultyFilter, typeFilter]);

  // Type filter chips reflect the actual question types available in the current result.
  const availableTypes = useMemo(() => {
    if (!questions) return [];
    return Array.from(new Set(questions.map((q) => q.question_type)));
  }, [questions]);

  const focusedQuestion = useMemo(
    () => questions?.find((q) => q.id === focusedQuestionId) ?? null,
    [questions, focusedQuestionId],
  );

  const selectedQuestions = useMemo(
    () => (questions ?? []).filter((q) => selectedQuestionIds.has(q.id)),
    [questions, selectedQuestionIds],
  );

  const toggleQuestion = (id: number) => {
    setSelectedQuestionIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const removeQuestion = (id: number) => {
    setSelectedQuestionIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  };

  const selectedChapter = chapters?.find((c) => c.id === selectedChapterId);
  const canSubmit =
    title.trim() !== '' &&
    selectedSubjectId !== '' &&
    selectedChapterId !== '' &&
    selectedQuestionIds.size > 0;

  const handleSubmit = async () => {
    if (!canSubmit || !selectedChapter) return;
    const result = await createProblemSet.mutateAsync({
      title: title.trim(),
      standard: selectedChapter.standard,
      subject: selectedSubjectId as number,
      chapter: selectedChapterId as number,
      estimated_minutes: estimatedMinutes ? parseInt(estimatedMinutes, 10) : null,
      question_ids: Array.from(selectedQuestionIds),
    });
    setSuccessId(result.id);
  };

  // ── Success state ────────────────────────────────────────────────────────
  if (successId !== null) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <EmptyState
          title="Problem set created!"
          description={
            <>
              <strong className="text-ink-700">{title}</strong> with{' '}
              <strong className="text-ink-700">{selectedQuestionIds.size}</strong>{' '}
              {selectedQuestionIds.size === 1 ? 'question' : 'questions'} is ready to assign.
            </>
          }
          action={
            <div className="flex flex-wrap justify-center gap-3">
              <Button onClick={() => navigate('/teacher/assignments/new')}>Assign it now</Button>
              <Button variant="ghost" onClick={() => navigate('/teacher')}>
                Back to dashboard
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  // ── Main UI ──────────────────────────────────────────────────────────────
  // Mobile: extra bottom padding leaves room for the sticky mobile action bar.
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 pb-28 lg:px-6 lg:pb-8">
      {/* Header */}
      <SectionHeading
        as="h1"
        eyebrow="Authoring"
        title="Build Problem Set"
        description="Group questions into an assignable set. Click a question to preview exactly how students will see it."
        action={
          <button
            type="button"
            onClick={() => navigate('/teacher')}
            className="text-sm font-medium text-ink-500 hover:text-ink-800"
          >
            ← Back
          </button>
        }
      />

      {/* Details card */}
      <Card className="space-y-4">
        <h2 className="font-display text-lg font-semibold text-ink-900">Details</h2>
        <Input
          label="Title"
          placeholder="e.g. Quadratic Equations Practice Set 1"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <div className="grid gap-3 sm:grid-cols-3">
          <Select
            label="Subject"
            value={selectedSubjectId}
            onChange={(e) => {
              setSelectedSubjectId(e.target.value ? Number(e.target.value) : '');
              setSelectedChapterId('');
              setSelectedQuestionIds(new Set());
              setFocusedQuestionId(null);
            }}
          >
            <option value="">Select subject…</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
          <Select
            label="Chapter"
            value={selectedChapterId}
            onChange={(e) => {
              setSelectedChapterId(e.target.value ? Number(e.target.value) : '');
              setSelectedQuestionIds(new Set());
              setFocusedQuestionId(null);
            }}
            disabled={!selectedSubjectId || !chapters}
          >
            <option value="">Select chapter…</option>
            {chapters?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} (Std {c.standard_number})
              </option>
            ))}
          </Select>
          <Input
            type="number"
            min={1}
            max={180}
            label="Estimated time (min)"
            placeholder="e.g. 30"
            value={estimatedMinutes}
            onChange={(e) => setEstimatedMinutes(e.target.value)}
          />
        </div>
      </Card>

      {/* Two-pane picker + preview */}
      <div className="grid gap-4 lg:grid-cols-12">
        {/* Picker (left) */}
        <Card className="!p-0 lg:col-span-5 xl:col-span-4">
          <div className="flex items-center justify-between border-b border-ink-100 px-5 py-4">
            <h2 className="font-display text-lg font-semibold text-ink-900">Select Questions</h2>
            {questions && (
              <span className="text-xs text-ink-400">
                {filteredQuestions.length} of {questions.length}
              </span>
            )}
          </div>

          {/* Filters */}
          {selectedSubjectId !== '' && (
            <div className="space-y-3 border-b border-ink-100 px-5 py-4">
              <Input
                placeholder="Search question text…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={
                  <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="7" cy="7" r="5" />
                    <path d="M11 11l4 4" strokeLinecap="round" />
                  </svg>
                }
              />
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="mr-1 text-xs font-medium text-ink-500">Difficulty:</span>
                <FilterChip
                  active={difficultyFilter === null}
                  onClick={() => setDifficultyFilter(null)}
                >
                  Any
                </FilterChip>
                {[1, 2, 3, 4, 5].map((d) => (
                  <FilterChip
                    key={d}
                    active={difficultyFilter === d}
                    onClick={() => setDifficultyFilter(difficultyFilter === d ? null : d)}
                    title={`${d}/5`}
                  >
                    <span className="tracking-tighter text-amber-500">{'★'.repeat(d)}</span>
                  </FilterChip>
                ))}
              </div>
              {availableTypes.length > 1 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="mr-1 text-xs font-medium text-ink-500">Type:</span>
                  <FilterChip active={typeFilter === null} onClick={() => setTypeFilter(null)}>
                    Any
                  </FilterChip>
                  {availableTypes.map((t) => (
                    <FilterChip
                      key={t}
                      active={typeFilter === t}
                      onClick={() => setTypeFilter(typeFilter === t ? null : t)}
                    >
                      {typeLabel(t)}
                    </FilterChip>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* List body */}
          <div className="p-3">
            {!selectedSubjectId ? (
              <p className="py-10 text-center text-sm text-ink-400">
                Select a subject to browse questions.
              </p>
            ) : questionsLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-lg" />
                ))}
              </div>
            ) : !questions || questions.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-sm text-ink-500">No questions found.</p>
                <button
                  type="button"
                  onClick={() => navigate('/teacher/questions/new')}
                  className="mt-2 text-sm font-medium text-brand-600 hover:text-brand-700"
                >
                  Author one →
                </button>
              </div>
            ) : filteredQuestions.length === 0 ? (
              <p className="py-10 text-center text-sm text-ink-400">
                No matches for the current filters.
              </p>
            ) : (
              <div className="max-h-[36rem] space-y-1.5 overflow-y-auto pr-1">
                {filteredQuestions.map((q) => (
                  <QuestionRow
                    key={q.id}
                    question={q}
                    selected={selectedQuestionIds.has(q.id)}
                    focused={focusedQuestionId === q.id}
                    onToggle={() => toggleQuestion(q.id)}
                    onFocus={() => setFocusedQuestionId(q.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Preview (right) */}
        <div className="lg:col-span-7 xl:col-span-8">
          {(() => {
            const isSelected = focusedQuestion
              ? selectedQuestionIds.has(focusedQuestion.id)
              : false;
            return (
              <QuestionPreviewPanel
                question={focusedQuestion}
                emptyTitle="Pick a question to preview"
                emptyDescription="Click any row on the left to see exactly how students will see it — full LaTeX, options, images, and all."
                footer={
                  focusedQuestion ? (
                    <>
                      <p className="text-xs text-ink-500">
                        {isSelected ? 'This question is in the set.' : 'Not in the set yet.'}
                      </p>
                      <Button
                        variant={isSelected ? 'ghost' : 'brand'}
                        size="sm"
                        onClick={() => toggleQuestion(focusedQuestion.id)}
                      >
                        {isSelected ? 'Remove from set' : '+ Add to set'}
                      </Button>
                    </>
                  ) : null
                }
              />
            );
          })()}
        </div>
      </div>

      {/* Selected questions strip */}
      <SelectedStrip selectedQuestions={selectedQuestions} onRemove={removeQuestion} />

      {/* Submit — desktop layout (inline action row). */}
      <div className="hidden flex-wrap items-center justify-end gap-3 border-t border-ink-100 pt-5 lg:flex">
        {!canSubmit && (
          <p className="text-xs text-ink-400">
            Fill in title, subject, chapter, and select at least one question.
          </p>
        )}
        {createProblemSet.isError && (
          <p className="text-xs font-medium text-rose-600">Failed to create. Please try again.</p>
        )}
        <Button
          size="lg"
          onClick={handleSubmit}
          disabled={!canSubmit || createProblemSet.isPending}
        >
          {createProblemSet.isPending && <LoadingSpinner size="sm" />}
          Create Problem Set
        </Button>
      </div>

      {/* Sticky mobile action bar — the inline submit lives at the bottom of
          a long page, requiring a lot of scrolling on phones. Surface the
          same action above the system nav so it's always one tap away. */}
      <div
        className="fixed inset-x-0 bottom-0 z-30 border-t border-ink-100 bg-paper/95 px-4 py-3 shadow-lift backdrop-blur lg:hidden"
        data-testid="mobile-create-bar"
      >
        {createProblemSet.isError && (
          <p className="mb-1.5 text-center text-xs font-medium text-rose-600">
            Failed to create. Please try again.
          </p>
        )}
        <Button
          size="lg"
          onClick={handleSubmit}
          disabled={!canSubmit || createProblemSet.isPending}
          className="w-full"
        >
          {createProblemSet.isPending && <LoadingSpinner size="sm" />}
          {createProblemSet.isPending ? 'Creating…' : `Create${selectedQuestionIds.size > 0 ? ` (${selectedQuestionIds.size})` : ''}`}
        </Button>
        {!canSubmit && (
          <p className="mt-1.5 text-center text-xs text-ink-500">
            Pick a subject, chapter, title, and at least one question.
          </p>
        )}
      </div>
    </div>
  );
};

// ── Sub-components ──────────────────────────────────────────────────────────

const FilterChip = ({
  active,
  onClick,
  title,
  children,
}: {
  active: boolean;
  onClick: () => void;
  title?: string;
  children: React.ReactNode;
}) => (
  <button
    type="button"
    onClick={onClick}
    title={title}
    className={[
      'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium transition-colors',
      active
        ? 'bg-brand-600 text-white shadow-soft'
        : 'bg-ink-50 text-ink-700 hover:bg-ink-100',
    ].join(' ')}
  >
    {children}
  </button>
);
