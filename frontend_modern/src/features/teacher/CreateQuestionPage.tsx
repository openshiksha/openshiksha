import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { LoadingSpinner, RichContent } from '@/shared/ui';
import { WidgetGalleryPanel } from './WidgetGalleryPanel';
import { getWidgetModule } from '@/widgets/registry';
import { useSubjectRooms } from './useSubjectRooms';
import { useChapters } from './useChapters';
import { useCreateQuestion } from './useCreateQuestion';
import { useUpdateQuestion } from './useUpdateQuestion';
import { useQuestion } from './useQuestion';
import { useGenerateQuestions } from './useGenerateQuestions';
import type {
  MCQOption,
  QuestionSubpartWrite,
  GeneratedQuestionDraft,
} from '@/types/index';

// ── IW-5: Widget picker section (gallery toggler + applied-widget summary) ──

interface WidgetPickerSectionProps {
  kind: string;
  config: Record<string, unknown>;
  onChange: (next: { kind: string; config: Record<string, unknown> }) => void;
}

/**
 * Collapsible block that surfaces the active subpart's interactive widget,
 * if any. When no widget is attached, shows a "+ Add interactive widget"
 * button that opens the `WidgetGalleryPanel`. When one is attached,
 * summarises it and offers Edit / Remove buttons.
 *
 * Kept tight so it doesn't dominate the author's view when widgets aren't
 * in use (the dominant case for short-answer / MCQ rows).
 */
function WidgetPickerSection({ kind, config, onChange }: WidgetPickerSectionProps) {
  const [galleryOpen, setGalleryOpen] = useState(false);
  const module = kind ? getWidgetModule(kind) : undefined;

  if (galleryOpen) {
    return (
      <WidgetGalleryPanel
        initialKind={kind || undefined}
        initialConfig={kind ? config : undefined}
        onApply={(sel) => {
          onChange(sel);
          setGalleryOpen(false);
        }}
        onCancel={() => setGalleryOpen(false)}
      />
    );
  }

  return (
    <div>
      <label className="block text-xs font-medium text-ink-600 mb-1">
        Interactive widget <span className="font-normal text-ink-400">(optional — renders in a sandbox)</span>
      </label>
      {kind ? (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-ink-200 bg-paper px-3 py-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink-900">
              {module?.meta.title ?? kind}
            </p>
            <p className="truncate font-mono text-[10px] uppercase tracking-wider text-ink-400">
              {kind} · {Object.keys(config).length} field{Object.keys(config).length === 1 ? '' : 's'} configured
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setGalleryOpen(true)}
              className="rounded-md border border-ink-200 px-2 py-1 text-xs hover:bg-ink-50"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => onChange({ kind: '', config: {} })}
              className="rounded-md border border-ink-200 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
            >
              Remove
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setGalleryOpen(true)}
          className="w-full rounded-lg border border-dashed border-ink-300 bg-paper px-3 py-2 text-sm text-ink-600 hover:border-brand-600 hover:text-brand-700"
        >
          + Add interactive widget
        </button>
      )}
    </div>
  );
}

type QuestionType = 'mcq' | 'fill_blank' | 'numeric' | 'multi_select';

type VariableSpec = { min: number; max: number; integer: boolean };

interface SubpartDraft {
  question_text: string;
  question_type: QuestionType;
  options: MCQOption[];
  correct_answer: string;
  variable_constraints: Record<string, VariableSpec>;
  image_url: string;
  solution_text: string;
  hint_text: string;
  /** IW-5: registry kind of an interactive widget attached to the subpart (blank = none). */
  widget_kind: string;
  /** IW-5: per-widget config validated against the kind's params schema. */
  widget_config: Record<string, unknown>;
}

const defaultSubpart = (): SubpartDraft => ({
  question_text: '',
  question_type: 'mcq',
  options: [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' },
  ],
  correct_answer: '',
  variable_constraints: {},
  image_url: '',
  solution_text: '',
  hint_text: '',
  widget_kind: '',
  widget_config: {},
});

// ---------------------------------------------------------------------------
// Variable token helpers
// ---------------------------------------------------------------------------

const extractTokens = (text: string): string[] => {
  const re = /\{\{(\w+)\}\}/g;
  const names = new Set<string>();
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) names.add(match[1]);
  return Array.from(names).sort();
};

const syncVariableConstraints = (
  text: string,
  existing: Record<string, VariableSpec>
): Record<string, VariableSpec> => {
  const tokens = extractTokens(text);
  const next: Record<string, VariableSpec> = {};
  for (const token of tokens) {
    next[token] = existing[token] ?? { min: 1, max: 10, integer: true };
  }
  return next;
};

// ---------------------------------------------------------------------------
// Live preview widget
// ---------------------------------------------------------------------------

const xorshift32 = (seed: number) => {
  let s = seed | 1;
  return () => {
    s ^= s << 13;
    s ^= s >> 17;
    s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };
};

const sampleValues = (
  constraints: Record<string, VariableSpec>,
  studentNum: number
): Record<string, number> => {
  const rng = xorshift32(studentNum * 31337);
  const out: Record<string, number> = {};
  for (const [name, spec] of Object.entries(constraints)) {
    const raw = rng() * (spec.max - spec.min) + spec.min;
    out[name] = spec.integer ? Math.round(raw) : parseFloat(raw.toFixed(2));
  }
  return out;
};

const substituteText = (text: string, values: Record<string, number>): string =>
  text.replace(/\{\{(\w+)\}\}/g, (_, name) =>
    values[name] !== undefined ? String(values[name]) : `{{${name}}}`
  );

const VariablePreview = ({
  constraints,
  questionText,
}: {
  constraints: Record<string, VariableSpec>;
  questionText: string;
}) => {
  if (!Object.keys(constraints).length) return null;
  const v1 = sampleValues(constraints, 1);
  const v2 = sampleValues(constraints, 2);
  return (
    <div className="mt-3 pt-3 border-t border-amber-200">
      <p className="text-xs font-semibold text-amber-900 mb-1">Preview</p>
      <p className="text-xs text-ink-600">Student A: {substituteText(questionText, v1)}</p>
      <p className="text-xs text-ink-600 mt-0.5">Student B: {substituteText(questionText, v2)}</p>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Live preview — RichContent renders the same HTML + LaTeX the student will see.
// ---------------------------------------------------------------------------

function renderPreview(text: string): React.ReactNode {
  if (!text) {
    return <span className="text-ink-400">Type question text above to see preview...</span>;
  }
  return <RichContent text={text} variant="block" />;
}

// ---------------------------------------------------------------------------
// Draft card (from AI generation)
// ---------------------------------------------------------------------------

const DraftCard = ({
  draft,
  onUse,
}: {
  draft: GeneratedQuestionDraft;
  onUse: (draft: GeneratedQuestionDraft) => void;
}) => (
  <div className="bg-white rounded-xl border border-ink-100 p-4">
    <div className="flex items-start justify-between gap-2 mb-2">
      <span className="text-xs font-semibold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
        Draft
      </span>
      <button
        onClick={() => onUse(draft)}
        className="text-xs bg-brand-600 text-white px-3 py-1 rounded-lg hover:bg-brand-700 transition-colors shrink-0"
      >
        Use this
      </button>
    </div>
    <p className="text-sm text-ink-800 font-mono leading-relaxed mb-2">
      {draft.question_text}
    </p>
    {draft.options && draft.options.length > 0 && (
      <div className="space-y-1 mb-2">
        {draft.options.map((opt) => (
          <div
            key={opt.key}
            className={`flex gap-2 text-xs ${opt.key === draft.correct_answer ? 'text-emerald-700 font-semibold' : 'text-ink-600'}`}
          >
            <span className="font-mono">{opt.key}.</span>
            <span>{opt.text}</span>
          </div>
        ))}
      </div>
    )}
    {!draft.options && (
      <p className="text-xs text-ink-500 mb-2">
        Answer: <span className="font-mono text-emerald-700">{draft.correct_answer}</span>
      </p>
    )}
    {draft.suggested_tags.length > 0 && (
      <div className="flex flex-wrap gap-1">
        {draft.suggested_tags.map((t) => (
          <span key={t} className="text-xs bg-ink-100 text-ink-500 px-2 py-0.5 rounded-full">{t}</span>
        ))}
      </div>
    )}
  </div>
);

// ---------------------------------------------------------------------------
// AI Generation Panel
// ---------------------------------------------------------------------------

const AIGenerationPanel = ({
  chapterId,
  onUseDraft,
}: {
  chapterId: number | '';
  onUseDraft: (draft: GeneratedQuestionDraft) => void;
}) => {
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState('');
  const [qType, setQType] = useState<QuestionType>('mcq');
  const [difficulty, setDifficulty] = useState(2);
  const [count, setCount] = useState(3);
  const [drafts, setDrafts] = useState<GeneratedQuestionDraft[]>([]);
  const [aiUnavailable, setAiUnavailable] = useState(false);

  const generateMutation = useGenerateQuestions();

  const handleGenerate = () => {
    if (!chapterId || !topic.trim()) return;
    setAiUnavailable(false);
    generateMutation.mutate(
      {
        topic: topic.trim(),
        chapter_id: chapterId as number,
        question_type: qType,
        difficulty,
        count,
      },
      {
        onSuccess: (data) => {
          setDrafts(data.questions);
          setAiUnavailable(!data.ai_available);
        },
      }
    );
  };

  return (
    <div className="bg-brand-50 rounded-xl border border-brand-200 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">✨</span>
          <span className="font-semibold text-brand-900 text-sm">Generate with AI</span>
          <span className="text-xs text-brand-700 font-normal">
            Draft questions from your topic and constraints
          </span>
        </div>
        <span className="text-brand-400 text-sm">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4 border-t border-brand-200">
          <div className="mt-4">
            <label className="block text-xs font-medium text-brand-800 mb-1">
              Topic or concept to test
            </label>
            <textarea
              rows={2}
              className="w-full border border-brand-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
              placeholder="e.g. Factoring quadratic polynomials, laws of thermodynamics…"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-brand-800 mb-1">Type</label>
              <select
                className="w-full border border-brand-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                value={qType}
                onChange={(e) => setQType(e.target.value as QuestionType)}
              >
                <option value="mcq">MCQ</option>
                <option value="numeric">Numeric</option>
                <option value="fill_blank">Fill blank</option>
                <option value="multi_select">Multi-select</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-brand-800 mb-1">Difficulty</label>
              <select
                className="w-full border border-brand-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                value={difficulty}
                onChange={(e) => setDifficulty(Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5].map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-brand-800 mb-1">Count</label>
              <select
                className="w-full border border-brand-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleGenerate}
              disabled={!chapterId || !topic.trim() || generateMutation.isPending}
              className="flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generateMutation.isPending ? (
                <>
                  <LoadingSpinner size="sm" />
                  Generating…
                </>
              ) : (
                '✨ Generate'
              )}
            </button>
            {generateMutation.isError && (
              <div className="flex items-center gap-2 text-xs text-rose-700">
                <span>Generation failed.</span>
                <button
                  onClick={handleGenerate}
                  className="underline hover:no-underline"
                >
                  Retry
                </button>
              </div>
            )}
          </div>

          {generateMutation.isPending && (
            <div className="space-y-2">
              {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="h-20 bg-brand-100 rounded-lg animate-pulse" />
              ))}
            </div>
          )}

          {!generateMutation.isPending && aiUnavailable && (
            <div className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-900">
              <span aria-hidden className="mt-px">⚠️</span>
              <p>
                AI question generation is unavailable right now. Please try again
                in a little while, or write your question by hand below.
              </p>
            </div>
          )}

          {!generateMutation.isPending && !aiUnavailable && drafts.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs font-semibold text-brand-900">
                {drafts.length} draft{drafts.length > 1 ? 's' : ''} — click "Use this" to pre-fill the form
              </p>
              {drafts.map((d, i) => (
                <DraftCard key={i} draft={d} onUse={onUseDraft} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export const CreateQuestionPage = ({ editMode = false }: { editMode?: boolean }) => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const editId = editMode && id ? Number(id) : undefined;

  const { data: subjectRooms } = useSubjectRooms();
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | ''>('');
  const [selectedChapterId, setSelectedChapterId] = useState<number | ''>('');
  const [difficulty, setDifficulty] = useState(2);
  const [subparts, setSubparts] = useState<SubpartDraft[]>([defaultSubpart()]);
  const [activeSubpart, setActiveSubpart] = useState(0);
  const [successId, setSuccessId] = useState<number | null>(null);

  const { data: chapters } = useChapters(
    selectedSubjectId !== '' ? selectedSubjectId : undefined,
  );
  const createQuestion = useCreateQuestion();
  const updateQuestion = useUpdateQuestion();
  const { data: existingQuestion, isLoading: loadingExisting } = useQuestion(editId);

  // Pre-fill form in edit mode when the loaded question changes (during render — react.dev/learn/you-might-not-need-an-effect)
  const [prefilledFrom, setPrefilledFrom] = useState<typeof existingQuestion | undefined>(undefined);
  if (editMode && existingQuestion && existingQuestion !== prefilledFrom) {
    setPrefilledFrom(existingQuestion);
    setSelectedSubjectId(existingQuestion.subject);
    setSelectedChapterId(existingQuestion.chapter);
    setDifficulty(existingQuestion.difficulty);
    setSubparts(
      existingQuestion.subparts.map((sp) => ({
        question_text: sp.question_text,
        question_type: existingQuestion.question_type as QuestionType,
        options: sp.options ?? [
          { key: 'A', text: '' },
          { key: 'B', text: '' },
          { key: 'C', text: '' },
          { key: 'D', text: '' },
        ],
        correct_answer: '',
        variable_constraints: {},
        image_url: sp.image_url ?? '',
        solution_text: sp.solution_text ?? '',
        hint_text: sp.hint_text ?? '',
        widget_kind: sp.widget_kind ?? '',
        widget_config: sp.widget_config ?? {},
      }))
    );
  }

  // Derive unique subjects from the teacher's subject rooms
  const subjects = Array.from(
    new Map(subjectRooms?.map((r) => [r.subject, { id: r.subject, name: r.subject_name }]) ?? []).values()
  );

  const updateSubpart = useCallback((idx: number, patch: Partial<SubpartDraft>) => {
    setSubparts((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  }, []);

  const handleTextChange = useCallback(
    (idx: number, value: string, currentConstraints: Record<string, VariableSpec>) => {
      updateSubpart(idx, {
        question_text: value,
        variable_constraints: syncVariableConstraints(value, currentConstraints),
      });
    },
    [updateSubpart]
  );

  const addSubpart = () => {
    setSubparts((prev) => [...prev, defaultSubpart()]);
    setActiveSubpart(subparts.length);
  };

  const removeSubpart = (idx: number) => {
    if (subparts.length === 1) return;
    setSubparts((prev) => prev.filter((_, i) => i !== idx));
    setActiveSubpart(Math.max(0, activeSubpart - 1));
  };

  const updateOption = (subpartIdx: number, optIdx: number, text: string) => {
    setSubparts((prev) =>
      prev.map((s, i) => {
        if (i !== subpartIdx) return s;
        const opts = s.options.map((o, oi) => (oi === optIdx ? { ...o, text } : o));
        return { ...s, options: opts };
      })
    );
  };

  // Pre-fill subparts from an AI draft
  const handleUseDraft = useCallback((draft: GeneratedQuestionDraft) => {
    const draftType = draft.options
      ? draft.correct_answer.includes(',')
        ? 'multi_select'
        : 'mcq'
      : 'numeric';

    const opts: MCQOption[] = draft.options?.length
      ? draft.options
      : [
          { key: 'A', text: '' },
          { key: 'B', text: '' },
          { key: 'C', text: '' },
          { key: 'D', text: '' },
        ];

    const vc: Record<string, VariableSpec> = {};
    if (draft.variable_constraints) {
      for (const [k, v] of Object.entries(draft.variable_constraints)) {
        vc[k] = {
          min: typeof v.min === 'number' ? v.min : 1,
          max: typeof v.max === 'number' ? v.max : 10,
          integer: typeof v.integer === 'boolean' ? v.integer : true,
        };
      }
    }

    setSubparts([
      {
        question_text: draft.question_text,
        question_type: draftType,
        options: opts,
        correct_answer: draft.correct_answer,
        variable_constraints: vc,
        image_url: '',
        solution_text: draft.solution ?? '',
        hint_text: '',
        widget_kind: '',
        widget_config: {},
      },
    ]);
    setActiveSubpart(0);
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  }, []);

  const canSubmit =
    selectedSubjectId !== '' &&
    selectedChapterId !== '' &&
    subparts.every((s) => s.question_text.trim() !== '');

  const handleSubmit = async () => {
    if (!canSubmit) return;

    const subpartsPayload: QuestionSubpartWrite[] = subparts.map((s, i) => ({
      index: i,
      question_text: s.question_text,
      options: s.question_type === 'mcq' || s.question_type === 'multi_select'
        ? s.options.filter((o) => o.text.trim() !== '')
        : null,
      correct_answer: { type: s.question_type, answer: s.correct_answer },
      variable_constraints: Object.keys(s.variable_constraints).length > 0
        ? s.variable_constraints
        : null,
      ...(s.image_url.trim() ? { image_url: s.image_url.trim() } : {}),
      ...(s.solution_text.trim() ? { solution_text: s.solution_text.trim() } : {}),
      ...(s.hint_text.trim() ? { hint_text: s.hint_text.trim() } : {}),
      // IW-5: only send widget fields when the teacher actually picked
      // one. Blank widget_kind on a row is the "no widget" signal — the
      // writable serializer's validator then short-circuits and leaves
      // widget_config as the default {}.
      ...(s.widget_kind ? { widget_kind: s.widget_kind, widget_config: s.widget_config } : {}),
    }));

    const chapter = chapters?.find((c) => c.id === selectedChapterId);

    if (editMode && editId) {
      const result = await updateQuestion.mutateAsync({
        id: editId,
        data: {
          standard: chapter?.standard ?? 1,
          subject: selectedSubjectId as number,
          chapter: selectedChapterId as number,
          question_type: subparts[0].question_type,
          difficulty,
          subparts: subpartsPayload,
        },
      });
      setSuccessId(result.id);
    } else {
      const result = await createQuestion.mutateAsync({
        standard: chapter?.standard ?? 1,
        subject: selectedSubjectId as number,
        chapter: selectedChapterId as number,
        question_type: subparts[0].question_type,
        difficulty,
        subparts: subpartsPayload,
      });
      setSuccessId(result.id);
    }
  };

  const isPending = createQuestion.isPending || updateQuestion.isPending;
  const isError = createQuestion.isError || updateQuestion.isError;

  if (editMode && loadingExisting) {
    return (
      <div className="flex items-center justify-center py-24">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (successId !== null) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 text-center">
        <div className="bg-white rounded-xl border border-ink-100 p-10">
          <div className="text-4xl mb-4">✓</div>
          <h2 className="font-display text-xl font-semibold text-ink-900 mb-2">
            Question {editMode ? 'updated' : 'created'}!
          </h2>
          <p className="text-sm text-ink-500 mb-6">
            Question #{successId} has been {editMode ? 'updated in' : 'added to'} the question bank.
          </p>
          <div className="flex gap-3 justify-center">
            {!editMode && (
              <button
                onClick={() => {
                  setSuccessId(null);
                  setSubparts([defaultSubpart()]);
                  setSelectedChapterId('');
                }}
                className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700"
              >
                Create another
              </button>
            )}
            <button
              onClick={() => navigate('/teacher/questions')}
              className="px-4 py-2 rounded-lg border border-ink-200 text-ink-700 text-sm font-medium hover:bg-ink-50"
            >
              Back to question bank
            </button>
          </div>
        </div>
      </div>
    );
  }

  const current = subparts[activeSubpart];
  const hasVariableTokens = Object.keys(current.variable_constraints).length > 0;
  const showVariablePanel =
    (current.question_type === 'numeric' || current.question_type === 'fill_blank') &&
    hasVariableTokens;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900">
            {editMode ? 'Edit Question' : 'Create Question'}
          </h1>
          <p className="text-sm text-ink-500 mt-1">
            {editMode
              ? 'Update this question in the shared question bank.'
              : 'Add a question to the shared question bank.'}
          </p>
        </div>
        <button
          onClick={() => navigate('/teacher/questions')}
          className="text-sm text-ink-500 hover:text-ink-700"
        >
          ← Back
        </button>
      </div>

      <div className="space-y-6">
        {/* Chapter selection */}
        <div className="bg-white rounded-xl border border-ink-100 p-5 space-y-4">
          <h2 className="font-semibold text-ink-800">Chapter</h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">Subject</label>
              <select
                className="w-full border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={selectedSubjectId}
                onChange={(e) => {
                  setSelectedSubjectId(e.target.value ? Number(e.target.value) : '');
                  setSelectedChapterId('');
                }}
              >
                <option value="">Select subject...</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">Chapter</label>
              <select
                className="w-full border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
                value={selectedChapterId}
                onChange={(e) => setSelectedChapterId(e.target.value ? Number(e.target.value) : '')}
                disabled={!selectedSubjectId || !chapters}
              >
                <option value="">Select chapter...</option>
                {chapters?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} (Std {c.standard_number})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-xs font-medium text-ink-600 mb-2">Difficulty</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((d) => (
                <button
                  key={d}
                  onClick={() => setDifficulty(d)}
                  className={`w-9 h-9 rounded-lg text-sm font-medium border transition-colors ${
                    difficulty === d
                      ? 'bg-brand-600 text-white border-brand-600'
                      : 'bg-white text-ink-600 border-ink-200 hover:border-brand-400'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <p className="text-xs text-ink-400 mt-1">1 = easiest, 5 = hardest</p>
          </div>
        </div>

        {/* AI Generation Panel — after chapter so chapterId is always set */}
        {!editMode && (
          <AIGenerationPanel
            chapterId={selectedChapterId}
            onUseDraft={handleUseDraft}
          />
        )}

        {/* Subpart tabs */}
        <div className="bg-white rounded-xl border border-ink-100 overflow-hidden">
          <div className="flex items-center border-b border-ink-100 px-5 pt-4 gap-2 overflow-x-auto">
            {subparts.map((_, i) => (
              <button
                key={i}
                onClick={() => setActiveSubpart(i)}
                className={`pb-3 px-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeSubpart === i
                    ? 'border-brand-600 text-brand-700'
                    : 'border-transparent text-ink-500 hover:text-ink-700'
                }`}
              >
                Part {String.fromCharCode(65 + i)}
              </button>
            ))}
            <button
              onClick={addSubpart}
              className="pb-3 px-3 text-sm text-brand-600 hover:text-brand-800 whitespace-nowrap"
            >
              + Add part
            </button>
          </div>

          <div className="p-5 space-y-4">
            {/* Question type */}
            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">Question type</label>
              <select
                className="border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={current.question_type}
                onChange={(e) =>
                  updateSubpart(activeSubpart, { question_type: e.target.value as QuestionType })
                }
              >
                <option value="mcq">Multiple choice (MCQ)</option>
                <option value="numeric">Numeric</option>
                <option value="fill_blank">Fill in the blank</option>
                <option value="multi_select">Multi-select</option>
              </select>
            </div>

            {/* Question text */}
            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">
                Question text{' '}
                <span className="text-ink-400">
                  {'(LaTeX: $x^2$ or $$\\frac{a}{b}$$)'}
                  {(current.question_type === 'numeric' || current.question_type === 'fill_blank') &&
                    ' · use {{a}} for variable tokens'}
                </span>
              </label>
              <textarea
                rows={3}
                className="w-full border border-ink-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder={
                  current.question_type === 'numeric' || current.question_type === 'fill_blank'
                    ? 'e.g. Solve ${{a}}x + {{b}} = {{c}}$'
                    : 'e.g. Solve $x^2 - 4 = 0$'
                }
                value={current.question_text}
                onChange={(e) =>
                  handleTextChange(activeSubpart, e.target.value, current.variable_constraints)
                }
              />
            </div>

            {/* Live KaTeX preview */}
            <div className="bg-ink-50 border border-ink-100 rounded-lg px-4 py-3 text-sm text-ink-800 min-h-[48px]">
              <span className="text-xs text-ink-400 block mb-1">Preview</span>
              {renderPreview(current.question_text)}
            </div>

            {/* Optional interactive widget (IW-5) */}
            <WidgetPickerSection
              kind={current.widget_kind}
              config={current.widget_config}
              onChange={(next) =>
                updateSubpart(activeSubpart, {
                  widget_kind: next.kind,
                  widget_config: next.config,
                })
              }
            />

            {/* Optional image URL */}
            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">
                Image URL <span className="font-normal text-ink-400">(optional — shown above question text)</span>
              </label>
              <input
                type="url"
                className="w-full border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="https://example.com/diagram.png"
                value={current.image_url}
                onChange={(e) => updateSubpart(activeSubpart, { image_url: e.target.value })}
              />
              {current.image_url.trim() && (
                <img
                  src={current.image_url}
                  alt="Preview"
                  className="mt-2 max-w-xs rounded border border-ink-100"
                  style={{ maxHeight: '160px', objectFit: 'contain' }}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">
                Worked solution <span className="font-normal text-ink-400">(optional — shown to students after grading)</span>
              </label>
              <textarea
                rows={3}
                className="w-full border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="Step-by-step solution. LaTeX with $...$ supported."
                value={current.solution_text}
                onChange={(e) => updateSubpart(activeSubpart, { solution_text: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">
                Hint <span className="font-normal text-ink-400">(optional — shown to struggling students during practice)</span>
              </label>
              <textarea
                rows={2}
                className="w-full border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="A nudge in the right direction."
                value={current.hint_text}
                onChange={(e) => updateSubpart(activeSubpart, { hint_text: e.target.value })}
              />
            </div>

            {/* Variable constraints panel */}
            {showVariablePanel && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h4 className="text-xs font-semibold text-amber-900 mb-3">
                  Variable Constraints
                  <span className="ml-1 font-normal text-amber-700">
                    {'— define the range for each {{token}} in your question'}
                  </span>
                </h4>
                <div className="space-y-2">
                  {Object.entries(current.variable_constraints).map(([name, spec]) => (
                    <div key={name} className="flex items-center gap-3 flex-wrap">
                      <span className="w-20 text-xs font-mono font-semibold text-amber-800">
                        {`{{${name}}}`}
                      </span>
                      <label className="text-xs text-ink-600">min</label>
                      <input
                        type="number"
                        value={spec.min}
                        onChange={(e) =>
                          updateSubpart(activeSubpart, {
                            variable_constraints: {
                              ...current.variable_constraints,
                              [name]: { ...spec, min: Number(e.target.value) },
                            },
                          })
                        }
                        className="w-20 text-xs border border-ink-200 rounded px-2 py-1"
                      />
                      <label className="text-xs text-ink-600">max</label>
                      <input
                        type="number"
                        value={spec.max}
                        onChange={(e) =>
                          updateSubpart(activeSubpart, {
                            variable_constraints: {
                              ...current.variable_constraints,
                              [name]: { ...spec, max: Number(e.target.value) },
                            },
                          })
                        }
                        className="w-20 text-xs border border-ink-200 rounded px-2 py-1"
                      />
                      <label className="flex items-center gap-1 text-xs text-ink-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={spec.integer}
                          onChange={(e) =>
                            updateSubpart(activeSubpart, {
                              variable_constraints: {
                                ...current.variable_constraints,
                                [name]: { ...spec, integer: e.target.checked },
                              },
                            })
                          }
                          className="rounded"
                        />
                        Integer
                      </label>
                    </div>
                  ))}
                </div>
                <VariablePreview
                  constraints={current.variable_constraints}
                  questionText={current.question_text}
                />
              </div>
            )}

            {/* MCQ options */}
            {(current.question_type === 'mcq' || current.question_type === 'multi_select') && (
              <div>
                <label className="block text-xs font-medium text-ink-600 mb-2">Options</label>
                <div className="space-y-2">
                  {current.options.map((opt, oi) => (
                    <div key={opt.key} className="flex items-center gap-2">
                      <span className="w-6 text-sm font-medium text-ink-500">{opt.key}</span>
                      <input
                        type="text"
                        className="flex-1 border border-ink-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                        placeholder={`Option ${opt.key}`}
                        value={opt.text}
                        onChange={(e) => updateOption(activeSubpart, oi, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Correct answer */}
            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1">
                Correct answer
                {hasVariableTokens && current.question_type === 'numeric' && (
                  <span className="ml-1 text-ink-400 font-normal">
                    {'(can use {{tokens}}, e.g. ({{c}} - {{b}}) / {{a}})'}
                  </span>
                )}
              </label>
              {current.question_type === 'mcq' ? (
                <select
                  className="border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  value={current.correct_answer}
                  onChange={(e) =>
                    updateSubpart(activeSubpart, { correct_answer: e.target.value })
                  }
                >
                  <option value="">Select correct option...</option>
                  {current.options.filter((o) => o.text.trim()).map((o) => (
                    <option key={o.key} value={o.key}>
                      {o.key}: {o.text}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  className="border border-ink-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder={current.question_type === 'numeric' ? 'e.g. 42' : 'Correct answer'}
                  value={current.correct_answer}
                  onChange={(e) =>
                    updateSubpart(activeSubpart, { correct_answer: e.target.value })
                  }
                />
              )}
            </div>

            {/* Remove subpart */}
            {subparts.length > 1 && (
              <button
                onClick={() => removeSubpart(activeSubpart)}
                className="text-xs text-rose-600 hover:text-rose-700"
              >
                Remove this part
              </button>
            )}
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || isPending}
            className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isPending && <LoadingSpinner size="sm" />}
            {editMode ? 'Update question' : 'Save question'}
          </button>
          {!canSubmit && (
            <p className="text-xs text-ink-400">
              Select a chapter and fill in all question text to save.
            </p>
          )}
          {isError && (
            <p className="text-xs text-rose-600">Failed to save. Please try again.</p>
          )}
        </div>
      </div>
    </div>
  );
};
