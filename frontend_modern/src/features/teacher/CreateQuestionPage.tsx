import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { useSubjectRooms } from './useSubjectRooms';
import { useChapters } from './useChapters';
import { useCreateQuestion } from './useCreateQuestion';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { MCQOption, QuestionSubpartWrite } from '@/types/index';

type QuestionType = 'mcq' | 'fill_blank' | 'numeric' | 'multi_select';

interface SubpartDraft {
  question_text: string;
  question_type: QuestionType;
  options: MCQOption[];
  correct_answer: string;
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
});

/** Render a single line of mixed LaTeX/plain text for the preview. */
function renderPreview(text: string): React.ReactNode {
  if (!text) return <span className="text-gray-400">Type question text above to see preview...</span>;
  const pattern = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g;
  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(<span key={`t-${lastIndex}`}>{text.slice(lastIndex, match.index)}</span>);
    }
    const raw = match[0];
    const isBlock = raw.startsWith('$$');
    const expr = isBlock ? raw.slice(2, -2) : raw.slice(1, -1);
    try {
      const html = katex.renderToString(expr, { throwOnError: false, displayMode: isBlock });
      nodes.push(
        <span
          key={`m-${match.index}`}
          dangerouslySetInnerHTML={{ __html: html }}
          className={isBlock ? 'block my-1' : 'inline'}
        />
      );
    } catch {
      nodes.push(<span key={`m-${match.index}`}>{raw}</span>);
    }
    lastIndex = match.index + raw.length;
  }
  if (lastIndex < text.length) nodes.push(<span key="t-end">{text.slice(lastIndex)}</span>);
  return <>{nodes}</>;
}

export const CreateQuestionPage = () => {
  const navigate = useNavigate();
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

  // Derive unique subjects and standards from the teacher's subject rooms
  const subjects = Array.from(
    new Map(subjectRooms?.map((r) => [r.subject, { id: r.subject, name: r.subject_name }]) ?? []).values()
  );
  // For standard, we need to parse it from classroom_display — use chapters or rooms
  // Rooms have classroom_display like "Standard 10 A". Use that to get standard info.
  // Actually, the SubjectRoom has `classroom` (number) not standard directly.
  // We'll let teachers pick subject first, then browse chapters across all standards.

  const updateSubpart = useCallback((idx: number, patch: Partial<SubpartDraft>) => {
    setSubparts((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)));
  }, []);

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
    }));

    // Derive standard from selected chapter
    const chapter = chapters?.find((c) => c.id === selectedChapterId);

    const result = await createQuestion.mutateAsync({
      standard: chapter?.standard ?? 1,
      subject: selectedSubjectId as number,
      chapter: selectedChapterId as number,
      question_type: subparts[0].question_type,
      difficulty,
      subparts: subpartsPayload,
    });

    setSuccessId(result.id);
  };

  if (successId !== null) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 text-center">
        <div className="bg-white rounded-xl border border-gray-200 p-10">
          <div className="text-4xl mb-4">✓</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Question created!</h2>
          <p className="text-sm text-gray-500 mb-6">Question #{successId} has been added to the question bank.</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => {
                setSuccessId(null);
                setSubparts([defaultSubpart()]);
                setSelectedChapterId('');
              }}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700"
            >
              Create another
            </button>
            <button
              onClick={() => navigate('/teacher')}
              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
            >
              Back to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  const current = subparts[activeSubpart];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Question</h1>
          <p className="text-sm text-gray-500 mt-1">Add a question to the shared question bank.</p>
        </div>
        <button
          onClick={() => navigate('/teacher')}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Back
        </button>
      </div>

      <div className="space-y-6">
        {/* Chapter selection */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Chapter</h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Subject</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
              <label className="block text-xs font-medium text-gray-600 mb-1">Chapter</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
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
            <label className="block text-xs font-medium text-gray-600 mb-2">Difficulty</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((d) => (
                <button
                  key={d}
                  onClick={() => setDifficulty(d)}
                  className={`w-9 h-9 rounded-lg text-sm font-medium border transition-colors ${
                    difficulty === d
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-1">1 = easiest, 5 = hardest</p>
          </div>
        </div>

        {/* Subpart tabs */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex items-center border-b border-gray-200 px-5 pt-4 gap-2 overflow-x-auto">
            {subparts.map((_, i) => (
              <button
                key={i}
                onClick={() => setActiveSubpart(i)}
                className={`pb-3 px-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeSubpart === i
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Part {String.fromCharCode(65 + i)}
              </button>
            ))}
            <button
              onClick={addSubpart}
              className="pb-3 px-3 text-sm text-indigo-500 hover:text-indigo-700 whitespace-nowrap"
            >
              + Add part
            </button>
          </div>

          <div className="p-5 space-y-4">
            {/* Question type */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Question type</label>
              <select
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={current.question_type}
                onChange={(e) => updateSubpart(activeSubpart, { question_type: e.target.value as QuestionType })}
              >
                <option value="mcq">Multiple choice (MCQ)</option>
                <option value="numeric">Numeric</option>
                <option value="fill_blank">Fill in the blank</option>
                <option value="multi_select">Multi-select</option>
              </select>
            </div>

            {/* Question text */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Question text <span className="text-gray-400">{'(LaTeX supported: $x^2$ or $$\\frac{a}{b}$$)'}</span>
              </label>
              <textarea
                rows={3}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g. Solve $x^2 - 4 = 0$"
                value={current.question_text}
                onChange={(e) => updateSubpart(activeSubpart, { question_text: e.target.value })}
              />
            </div>

            {/* Live KaTeX preview */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-800 min-h-[48px]">
              <span className="text-xs text-gray-400 block mb-1">Preview</span>
              {renderPreview(current.question_text)}
            </div>

            {/* MCQ options */}
            {(current.question_type === 'mcq' || current.question_type === 'multi_select') && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">Options</label>
                <div className="space-y-2">
                  {current.options.map((opt, oi) => (
                    <div key={opt.key} className="flex items-center gap-2">
                      <span className="w-6 text-sm font-medium text-gray-500">{opt.key}</span>
                      <input
                        type="text"
                        className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
              <label className="block text-xs font-medium text-gray-600 mb-1">Correct answer</label>
              {current.question_type === 'mcq' ? (
                <select
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={current.correct_answer}
                  onChange={(e) => updateSubpart(activeSubpart, { correct_answer: e.target.value })}
                >
                  <option value="">Select correct option...</option>
                  {current.options.filter((o) => o.text.trim()).map((o) => (
                    <option key={o.key} value={o.key}>{o.key}: {o.text}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder={current.question_type === 'numeric' ? 'e.g. 42' : 'Correct answer'}
                  value={current.correct_answer}
                  onChange={(e) => updateSubpart(activeSubpart, { correct_answer: e.target.value })}
                />
              )}
            </div>

            {/* Remove subpart */}
            {subparts.length > 1 && (
              <button
                onClick={() => removeSubpart(activeSubpart)}
                className="text-xs text-red-500 hover:text-red-700"
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
            disabled={!canSubmit || createQuestion.isPending}
            className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {createQuestion.isPending && <LoadingSpinner size="sm" />}
            Save question
          </button>
          {!canSubmit && (
            <p className="text-xs text-gray-400">Select a chapter and fill in all question text to save.</p>
          )}
          {createQuestion.isError && (
            <p className="text-xs text-red-500">Failed to save. Please try again.</p>
          )}
        </div>
      </div>
    </div>
  );
};
