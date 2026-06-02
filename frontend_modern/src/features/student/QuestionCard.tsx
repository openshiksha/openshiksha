import { useCallback, useState } from 'react';
import type { Question, QuestionSubpart, MCQOption, AIHint, SubpartType } from '@/types/index';
import { RichContent, InteractiveWidget } from '@/shared/ui';
import { useHints } from './useHints';

interface QuestionCardProps {
  question: Question;
  questionNumber: number;
  answers: Record<string, string>;
  onAnswerChange: (subpartId: number, value: string) => void;
  isSubmitted: boolean;
}

/**
 * Collapsible reveal for hints (during practice) and worked solutions
 * (after grading). Kept collapsed by default so it never spoils the answer
 * before the student has tried.
 */
function CollapsibleReveal({
  label,
  content,
  tone,
}: {
  label: string;
  content: string;
  tone: 'hint' | 'solution';
}) {
  const [open, setOpen] = useState(false);
  const styles =
    tone === 'solution'
      ? { btn: 'text-indigo-700 hover:text-indigo-900', box: 'bg-indigo-50 border-indigo-100' }
      : { btn: 'text-amber-700 hover:text-amber-900', box: 'bg-amber-50 border-amber-100' };

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`text-xs font-medium transition-colors ${styles.btn}`}
      >
        {open ? '▾' : '▸'} {label}
      </button>
      {open && (
        <div className={`mt-2 rounded-lg border p-3 text-sm text-gray-800 leading-relaxed ${styles.box}`}>
          <RichContent text={content} variant="block" />
        </div>
      )}
    </div>
  );
}

/**
 * Progressive AI hint panel shown during practice. On first request it fetches
 * the cached (or freshly generated) hint sequence for the subpart, then reveals
 * one hint at a time so the student is nudged gradually rather than handed the
 * whole chain at once. Hints never contain the correct answer.
 */
function AIHintPanel({ subpartId }: { subpartId: number }) {
  const { mutate, data, isPending, isError } = useHints();
  const [revealed, setRevealed] = useState(0);

  const hints: AIHint[] = data?.hints ?? [];
  const started = isPending || isError || data != null;

  const handleStart = () => {
    if (data) {
      setRevealed((n) => Math.min(n + 1, hints.length));
      return;
    }
    mutate(
      { subpart_id: subpartId },
      { onSuccess: () => setRevealed(1) }
    );
  };

  if (!started) {
    return (
      <div className="mt-3">
        <button
          type="button"
          onClick={handleStart}
          className="text-xs font-medium text-amber-700 hover:text-amber-900 transition-colors"
        >
          💡 Get a hint
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3">
      {isPending && <p className="text-xs text-gray-500">Thinking of a good hint…</p>}

      {isError && (
        <p className="text-xs text-red-600">
          Couldn&apos;t load a hint right now. Please try again.
        </p>
      )}

      {hints.slice(0, revealed).map((hint) => (
        <div
          key={hint.level}
          className="mt-2 rounded-lg border border-amber-100 bg-amber-50 p-3 text-sm text-gray-800 leading-relaxed"
        >
          <span className="mr-1 font-medium text-amber-700">Hint {hint.level}:</span>
          <RichContent text={hint.text} />
        </div>
      ))}

      {data && revealed < hints.length && (
        <button
          type="button"
          onClick={() => setRevealed((n) => Math.min(n + 1, hints.length))}
          className="mt-2 text-xs font-medium text-amber-700 hover:text-amber-900 transition-colors"
        >
          ▸ Show next hint ({revealed}/{hints.length})
        </button>
      )}

      {data && revealed >= hints.length && hints.length > 0 && (
        <p className="mt-2 text-xs text-gray-400">That&apos;s all the hints — give it a try!</p>
      )}
    </div>
  );
}

interface SubpartInputProps {
  subpart: QuestionSubpart;
  /** Effective answer type for this subpart (subpart_type, falling back to the
   *  question's type). Drives which input widget renders. */
  widgetType: SubpartType | 'compound';
  value: string;
  onChange: (value: string) => void;
  isSubmitted: boolean;
}

function SubpartInput({ subpart, widgetType, value, onChange, isSubmitted }: SubpartInputProps) {
  if (widgetType === 'mcq' && subpart.options) {
    return (
      <div className="space-y-2 mt-3">
        {subpart.options.map((opt: MCQOption) => (
          <label
            key={opt.key}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              value === opt.key
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            } ${isSubmitted ? 'cursor-not-allowed opacity-75' : ''}`}
          >
            <input
              type="radio"
              name={`subpart-${subpart.id}`}
              value={opt.key}
              checked={value === opt.key}
              onChange={() => !isSubmitted && onChange(opt.key)}
              disabled={isSubmitted}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-800">
              <strong className="mr-1">{opt.key}.</strong>
              <RichContent text={opt.text} />
            </span>
          </label>
        ))}
      </div>
    );
  }

  if (widgetType === 'multi_select' && subpart.options) {
    const selected = value ? value.split(',') : [];
    const toggle = (key: string) => {
      if (isSubmitted) return;
      const updated = selected.includes(key)
        ? selected.filter((k) => k !== key)
        : [...selected, key];
      onChange(updated.join(','));
    };

    return (
      <div className="space-y-2 mt-3">
        {subpart.options.map((opt: MCQOption) => (
          <label
            key={opt.key}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              selected.includes(opt.key)
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            } ${isSubmitted ? 'cursor-not-allowed opacity-75' : ''}`}
          >
            <input
              type="checkbox"
              value={opt.key}
              checked={selected.includes(opt.key)}
              onChange={() => toggle(opt.key)}
              disabled={isSubmitted}
              className="text-indigo-600 focus:ring-indigo-500 rounded"
            />
            <span className="text-sm text-gray-800">
              <strong className="mr-1">{opt.key}.</strong>
              <RichContent text={opt.text} />
            </span>
          </label>
        ))}
      </div>
    );
  }

  if (widgetType === 'numeric') {
    return (
      <input
        type="number"
        value={value}
        onChange={(e) => !isSubmitted && onChange(e.target.value)}
        disabled={isSubmitted}
        placeholder="Enter your answer"
        className="mt-3 block w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-indigo-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
      />
    );
  }

  // fill_blank and fallback
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => !isSubmitted && onChange(e.target.value)}
      disabled={isSubmitted}
      placeholder="Enter your answer"
      className="mt-3 block w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-indigo-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
    />
  );
}

export const QuestionCard = ({
  question,
  questionNumber,
  answers,
  onAnswerChange,
  isSubmitted,
}: QuestionCardProps) => {
  const handleChange = useCallback(
    (subpartId: number, value: string) => onAnswerChange(subpartId, value),
    [onAnswerChange]
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center">
          {questionNumber}
        </span>
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
          {question.question_type.replace('_', ' ')}
          {question.difficulty != null && ` · Difficulty ${question.difficulty}`}
        </span>
      </div>

      {question.stem_text && (
        <div className="mb-4 rounded-lg bg-ink-50 border border-ink-100 p-3 text-sm leading-relaxed text-ink-900">
          <RichContent text={question.stem_text} variant="block" />
        </div>
      )}

      {question.subparts.map((subpart, i) => {
        const value = answers[String(subpart.id)] ?? '';
        const isAnswered = value.trim().length > 0;

        return (
          <div key={subpart.id} className={i > 0 ? 'mt-6 pt-6 border-t border-gray-100' : ''}>
            {question.subparts.length > 1 && (
              <p className="text-xs text-gray-400 mb-1">Part {String.fromCharCode(97 + i)})</p>
            )}

            {subpart.image_url && (
              <div className="mb-3">
                <img
                  src={subpart.image_url}
                  alt="Question diagram"
                  className="max-w-full rounded border border-gray-200"
                  style={{ maxHeight: '320px', objectFit: 'contain' }}
                  loading="lazy"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              </div>
            )}

            {subpart.is_interactive && subpart.interactive_html ? (
              // M7-11: authored interactive widget runs in a sandboxed iframe;
              // falls back to the sanitised prompt if the widget HTML is absent.
              <InteractiveWidget
                html={subpart.interactive_html}
                fallbackText={subpart.question_text}
                className="text-sm text-gray-800"
              />
            ) : subpart.question_text ? (
              <RichContent
                text={subpart.question_text}
                variant="block"
                className="text-sm text-gray-800"
              />
            ) : (
              <p className="text-sm text-gray-400 italic">No question text available.</p>
            )}

            <SubpartInput
              subpart={subpart}
              widgetType={subpart.subpart_type || question.question_type}
              value={value}
              onChange={(val) => handleChange(subpart.id, val)}
              isSubmitted={isSubmitted}
            />

            {isAnswered && !isSubmitted && (
              <p className="text-xs text-green-600 mt-1">Answered</p>
            )}

            {!isSubmitted && <AIHintPanel subpartId={subpart.id} />}

            {isSubmitted && subpart.solution_text && (
              <CollapsibleReveal
                label="Show worked solution"
                content={subpart.solution_text}
                tone="solution"
              />
            )}
          </div>
        );
      })}
    </div>
  );
};
