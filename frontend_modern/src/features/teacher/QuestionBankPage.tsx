import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuestionList } from './useQuestionList';
import { useSubjects } from './useSubjects';
import { useChapters } from './useChapters';
import { useProblemSets } from './useProblemSets';
import { useAddQuestionToProblemSet } from './useAddQuestionToProblemSet';
import { previewFromQuestionText } from './previewFromQuestionText';
import { QuestionPreviewPanel } from './QuestionPreviewPanel';
import { difficultyStars, localizedTypeLabel, typeTone } from './questionPreviewMeta';
import { useT } from '@/shared/i18n';
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
  const t = useT();
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
          <Badge tone={typeTone(question.question_type)}>
            {localizedTypeLabel(t, question.question_type)}
          </Badge>
          <span className="text-xs tracking-wider text-amber-500" title={t('qbank.difficultyTitle', { level: question.difficulty })}>
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
        {t('qbank.rowEdit')}
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
  const t = useT();
  const [selectedPsId, setSelectedPsId] = useState<number | null>(null);
  const { data: problemSets, isLoading } = useProblemSets(question.subject);
  const addQuestion = useAddQuestionToProblemSet();
  const [success, setSuccess] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Lock body scroll + listen for ESC to close (a11y: AAA modal dialog pattern).
  useEffect(() => {
    const original = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    // Move focus into the dialog so a screen reader announces it.
    closeButtonRef.current?.focus();
    return () => {
      document.body.style.overflow = original;
      document.removeEventListener('keydown', onKey);
    };
  }, [onClose]);

  const handleAdd = () => {
    if (!selectedPsId) return;
    addQuestion.mutate(
      { problemSetId: selectedPsId, questionId: question.id },
      { onSuccess: () => setSuccess(true) },
    );
  };

  return (
    // Backdrop click-to-dismiss is a pointer-only convenience; keyboard users
    // close via Escape (handled in the effect above) or the panel's own close
    // control, so no key handler is needed on the overlay itself.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events
    <div
      className="fixed inset-0 z-50 flex justify-end bg-ink-900/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-to-set-title"
        className="flex h-full w-full max-w-md flex-col bg-paper shadow-lift"
      >
        <div className="flex items-center justify-between border-b border-ink-100 px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-brand-700">
              {t('addToSet.eyebrow')}
            </p>
            <h3
              id="add-to-set-title"
              className="font-display text-lg font-semibold text-ink-900"
            >
              {t('addToSet.questionTitle', { id: question.id })}
            </h3>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label={t('addToSet.closeLabel')}
            className="rounded-full p-1.5 text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            <svg viewBox="0 0 16 16" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {success ? (
            <EmptyState
              title={t('addToSet.addedTitle')}
              description={t('addToSet.addedDesc')}
              action={
                <div className="flex flex-wrap justify-center gap-3">
                  <Button onClick={onClose}>{t('addToSet.done')}</Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setSuccess(false);
                      setSelectedPsId(null);
                    }}
                  >
                    {t('addToSet.addAnother')}
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
                {t('addToSet.noSets', { subject: question.subject_name ?? t('addToSet.thisSubject') })}
              </p>
              <Button size="sm" className="mt-3" onClick={onClose}>
                {t('addToSet.buildOne')}
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
                        {t(
                          ps.question_count === 1
                            ? 'addToSet.questionsCountOne'
                            : 'addToSet.questionsCountMany',
                          { count: ps.question_count },
                        )}
                      </Badge>
                      {ps.estimated_minutes && (
                        <span className="text-xs text-ink-500">
                          {t('teacher.minutesApprox', { minutes: ps.estimated_minutes })}
                        </span>
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
                {t('addToSet.failedToAdd')}
              </p>
            )}
            <Button variant="ghost" onClick={onClose}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleAdd} disabled={!selectedPsId || addQuestion.isPending}>
              {addQuestion.isPending && <LoadingSpinner size="sm" />}
              {t('addToSet.add')}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

// ── Page ────────────────────────────────────────────────────────────────────

/**
 * TW-6: filter state lives in the URL so the back-button restores the same
 * search after the teacher visits the editor or set builder. Keys are short
 * (`q`, `subject`, `chapter`, `diff`, `focus`) to keep the URL tidy.
 */
const numberOrEmpty = (raw: string | null): number | '' => {
  if (!raw) return '';
  const n = Number(raw);
  return Number.isFinite(n) ? n : '';
};

export const QuestionBankPage = () => {
  const t = useT();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const search = searchParams.get('q') ?? '';
  const selectedSubject = numberOrEmpty(searchParams.get('subject'));
  const selectedChapter = numberOrEmpty(searchParams.get('chapter'));
  const selectedDifficulty = numberOrEmpty(searchParams.get('diff'));
  const focusedQuestionId = (() => {
    const raw = searchParams.get('focus');
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  })();

  // useDeferredValue gives us "debounce-ish" behaviour without an effect:
  // search updates the URL immediately for back/forward to round-trip,
  // and the heavy filtered query reads `deferredSearch` which lags behind
  // until rendering catches up.
  const deferredSearch = useDeferredValue(search);
  const [modalQuestion, setModalQuestion] = useState<Question | null>(null);

  // Merge-style URL updater — pass `null` to remove a key.
  const updateParams = (patch: Record<string, string | number | null | ''>) => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(patch)) {
          if (value === null || value === '') next.delete(key);
          else next.set(key, String(value));
        }
        return next;
      },
      { replace: true },
    );
  };

  const setSearch = (value: string) => updateParams({ q: value });
  const setSelectedSubject = (value: number | '') =>
    updateParams({ subject: value, chapter: null });
  const setSelectedChapter = (value: number | '') => updateParams({ chapter: value });
  const setSelectedDifficulty = (value: number | '') => updateParams({ diff: value });
  const setFocusedQuestionId = (value: number | null) => updateParams({ focus: value });

  const { data: subjects } = useSubjects();
  // Chapter list is scoped to the selected subject; disabled until a subject
  // is picked (otherwise it would offer chapters from across every subject
  // the teacher can see, which makes the picker overwhelming).
  const { data: chapters } = useChapters(
    selectedSubject !== '' ? (selectedSubject as number) : undefined,
  );
  const { data: questions, isLoading } = useQuestionList({
    search: deferredSearch || undefined,
    subject: selectedSubject !== '' ? (selectedSubject as number) : undefined,
    chapter: selectedChapter !== '' ? (selectedChapter as number) : undefined,
    difficulty: selectedDifficulty !== '' ? (selectedDifficulty as number) : undefined,
  });

  const handleSearchChange = (value: string) => setSearch(value);

  // Pass current URL state forward so the editor / set builder can return here.
  const currentReturnTo = `/teacher/questions?${searchParams.toString()}`;

  const hasFilters =
    !!search ||
    selectedSubject !== '' ||
    selectedChapter !== '' ||
    selectedDifficulty !== '';

  const clearFilters = () => {
    setSearchParams(new URLSearchParams(), { replace: true });
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
        eyebrow={t('qbank.eyebrow')}
        title={t('qbank.title')}
        description={t('qbank.description')}
        action={
          <Button onClick={() => navigate('/teacher/questions/new')}>{t('qbank.createQuestion')}</Button>
        }
      />

      {/* Two-pane: filters + list (left) · preview (right) */}
      <div className="grid gap-4 lg:grid-cols-12">
        {/* List column */}
        <Card className="!p-0 lg:col-span-5 xl:col-span-4">
          {/* Filter bar */}
          <div className="space-y-3 border-b border-ink-100 px-5 py-4">
            <Input
              placeholder={t('qbank.searchPlaceholder')}
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
                onChange={(e) => {
                  const next = e.target.value ? Number(e.target.value) : '';
                  setSelectedSubject(next);
                  // Chapter belongs to a subject — drop the selection when the
                  // subject changes so we don't filter against a stale chapter id.
                  setSelectedChapter('');
                }}
              >
                <option value="">{t('qbank.allSubjects')}</option>
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
                <option value="">{t('qbank.anyDifficulty')}</option>
                {[1, 2, 3, 4, 5].map((d) => (
                  <option key={d} value={d}>
                    {t('qbank.difficultyOption', { stars: '★'.repeat(d), level: d })}
                  </option>
                ))}
              </Select>
            </div>
            <Select
              value={selectedChapter}
              onChange={(e) =>
                setSelectedChapter(e.target.value ? Number(e.target.value) : '')
              }
              disabled={selectedSubject === ''}
              hint={selectedSubject === '' ? t('qbank.pickSubjectFirst') : undefined}
            >
              <option value="">{t('qbank.allChapters')}</option>
              {(chapters ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {c.standard_number !== undefined
                    ? ` · ${t('qbank.gradeSuffix', { grade: c.standard_number })}`
                    : ''}
                </option>
              ))}
            </Select>
            {hasFilters && (
              <button
                type="button"
                onClick={clearFilters}
                className="text-xs font-medium text-ink-500 hover:text-ink-800"
              >
                {t('qbank.clearFilters')}
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
                <p className="text-sm text-ink-500">{t('qbank.noQuestionsFound')}</p>
                <p className="mt-1 text-xs text-ink-400">
                  {hasFilters ? t('qbank.adjustFilters') : t('qbank.authorFirst')}
                </p>
                {!hasFilters && (
                  <Button
                    size="sm"
                    className="mt-3"
                    onClick={() => navigate('/teacher/questions/new')}
                  >
                    {t('qbank.createAQuestion')}
                  </Button>
                )}
              </div>
            ) : (
              <>
                <p className="px-3 pt-1 pb-2 text-xs text-ink-400">
                  {t(
                    questions.length === 1 ? 'qbank.resultsCountOne' : 'qbank.resultsCountMany',
                    { count: questions.length },
                  )}
                </p>
                <div className="max-h-[40rem] space-y-1.5 overflow-y-auto pr-1">
                  {questions.map((q) => (
                    <QuestionRow
                      key={q.id}
                      question={q}
                      focused={focusedQuestionId === q.id}
                      onFocus={() => setFocusedQuestionId(q.id)}
                      onEdit={() =>
                        navigate(
                          `/teacher/questions/${q.id}/edit?returnTo=${encodeURIComponent(currentReturnTo)}`,
                        )
                      }
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
            emptyTitle={t('qbank.previewEmptyTitle')}
            emptyDescription={t('qbank.previewEmptyDesc')}
            footer={
              focusedQuestion ? (
                <>
                  <p className="text-xs text-ink-500">
                    {t('qbank.reuseNote')}
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        navigate(
                          `/teacher/questions/${focusedQuestion.id}/edit?returnTo=${encodeURIComponent(currentReturnTo)}`,
                        )
                      }
                    >
                      {t('qbank.rowEdit')}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        navigate(
                          `/teacher/problem-sets/new?seedQuestion=${focusedQuestion.id}&returnTo=${encodeURIComponent(currentReturnTo)}`,
                        )
                      }
                    >
                      {t('qbank.useInNewSet')}
                    </Button>
                    <Button size="sm" onClick={() => setModalQuestion(focusedQuestion)}>
                      {t('qbank.addToProblemSet')}
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
