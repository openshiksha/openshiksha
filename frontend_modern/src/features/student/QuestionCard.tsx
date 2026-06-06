import { useCallback, useState } from 'react';
import type { Question, QuestionSubpart, MCQOption, AIHint, SubpartType } from '@/types/index';
import { RichContent, InteractiveWidget } from '@/shared/ui';
import { getWidgetModule } from '@/widgets/registry';
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
  // Worked solutions feel like "unlocking" the answer → brand-tinted panel.
  // Hints stay amber so students recognise them as guidance, not the answer.
  const styles =
    tone === 'solution'
      ? { btn: 'text-brand-700 hover:text-brand-800', box: 'bg-brand-50 border-brand-100' }
      : { btn: 'text-amber-800 hover:text-amber-900', box: 'bg-amber-50 border-amber-100' };

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`text-xs font-medium transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline ${styles.btn}`}
      >
        {open ? '▾' : '▸'} {label}
      </button>
      {open && (
        <div
          className={`mt-2 rounded-lg border p-3 text-sm text-ink-800 leading-relaxed ${styles.box}`}
        >
          <RichContent text={content} variant="block" />
        </div>
      )}
    </div>
  );
}

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
    mutate({ subpart_id: subpartId }, { onSuccess: () => setRevealed(1) });
  };

  if (!started) {
    return (
      <div className="mt-3">
        <button
          type="button"
          onClick={handleStart}
          className="text-xs font-medium text-amber-800 hover:text-amber-900 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline"
        >
          💡 Get a hint
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3">
      {isPending && <p className="text-xs text-ink-500">Thinking of a good hint…</p>}

      {isError && (
        <p className="text-xs text-rose-600">
          Couldn&apos;t load a hint right now. Please try again.
        </p>
      )}

      {hints.slice(0, revealed).map((hint) => (
        <div
          key={hint.level}
          className="mt-2 rounded-lg border border-amber-100 bg-amber-50 p-3 text-sm text-ink-800 leading-relaxed"
        >
          <span className="mr-1 font-medium text-amber-800">Hint {hint.level}:</span>
          <RichContent text={hint.text} />
        </div>
      ))}

      {data && revealed < hints.length && (
        <button
          type="button"
          onClick={() => setRevealed((n) => Math.min(n + 1, hints.length))}
          className="mt-2 text-xs font-medium text-amber-800 hover:text-amber-900 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline"
        >
          ▸ Show next hint ({revealed}/{hints.length})
        </button>
      )}

      {data && revealed >= hints.length && hints.length > 0 && (
        <p className="mt-2 text-xs text-ink-400">That&apos;s all the hints — give it a try!</p>
      )}
    </div>
  );
}

interface SubpartInputProps {
  subpart: QuestionSubpart;
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
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors motion-reduce:transition-none ${
              value === opt.key
                ? 'border-brand-500 bg-brand-50'
                : 'border-ink-200 hover:border-ink-300 hover:bg-ink-50'
            } ${isSubmitted ? 'cursor-not-allowed opacity-75' : ''}`}
          >
            <input
              type="radio"
              name={`subpart-${subpart.id}`}
              value={opt.key}
              checked={value === opt.key}
              onChange={() => !isSubmitted && onChange(opt.key)}
              disabled={isSubmitted}
              className="text-brand-600 focus:ring-brand-500"
            />
            <span className="text-sm text-ink-800">
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
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors motion-reduce:transition-none ${
              selected.includes(opt.key)
                ? 'border-brand-500 bg-brand-50'
                : 'border-ink-200 hover:border-ink-300 hover:bg-ink-50'
            } ${isSubmitted ? 'cursor-not-allowed opacity-75' : ''}`}
          >
            <input
              type="checkbox"
              value={opt.key}
              checked={selected.includes(opt.key)}
              onChange={() => toggle(opt.key)}
              disabled={isSubmitted}
              className="text-brand-600 focus:ring-brand-500 rounded"
            />
            <span className="text-sm text-ink-800">
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
        className="input-brand mt-3 max-w-xs disabled:cursor-not-allowed"
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
      className="input-brand mt-3 max-w-sm disabled:cursor-not-allowed"
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
    [onAnswerChange],
  );

  return (
    <div className="os-card p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-100 text-brand-700 text-xs font-bold flex items-center justify-center font-display">
          {questionNumber}
        </span>
        <span className="text-xs font-medium text-ink-400 uppercase tracking-wide">
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
        // IW-4: a widget whose module declares `meta.answerProducing` is
        // the answer surface — it owns the input and reports values via
        // ctx.reportValue. In that case the typed SubpartInput would be
        // a confusing parallel field, so we hide it. Explanatory widgets
        // (thermo-piston, custom-html) leave the typed input visible.
        const widgetModule = subpart.widget_kind ? getWidgetModule(subpart.widget_kind) : undefined;
        const widgetProducesAnswer = widgetModule?.meta.answerProducing === true;

        return (
          <div key={subpart.id} className={i > 0 ? 'mt-6 pt-6 border-t border-ink-100' : ''}>
            {question.subparts.length > 1 && (
              <p className="text-xs text-ink-400 mb-1">Part {String.fromCharCode(97 + i)})</p>
            )}

            {subpart.image_url && (
              <div className="mb-3">
                <img
                  src={subpart.image_url}
                  alt="Question diagram"
                  className="max-w-full rounded border border-ink-200"
                  style={{ maxHeight: '320px', objectFit: 'contain' }}
                  loading="lazy"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            )}

            {/*
              Widget render-path priority:
                1. widget_kind (Interactive Widgets Framework — kind-based,
                   the going-forward path; covers thermo-piston, custom-html,
                   future answer-producing widgets). The question prompt
                   renders ABOVE the widget because new-style widgets only
                   carry the interactive surface, not the prompt copy (the
                   legacy interactive_html embedded both in one blob).
                2. interactive_html (DEPRECATED M7-11 raw-HTML escape hatch;
                   prompt was historically embedded inside the HTML, so
                   question_text is only a fallback).
                3. plain RichContent fallback for text-only subparts.
            */}
            {subpart.widget_kind ? (
              <>
                {subpart.question_text && (
                  <RichContent
                    text={subpart.question_text}
                    variant="block"
                    className="text-sm text-ink-800"
                  />
                )}
                <InteractiveWidget
                  kind={subpart.widget_kind}
                  config={subpart.widget_config ?? {}}
                  fallbackText={subpart.question_text}
                  className="text-sm text-ink-800"
                  // IW-4: answer-producing widgets push their value through
                  // the typed `value` postMessage; we route it straight into
                  // the answer state via handleChange. The value is `unknown`
                  // at the protocol boundary — coerce to string here because
                  // `answers` is `Record<string, string>` (the submission
                  // payload's wire type).
                  onValue={
                    widgetProducesAnswer
                      ? (v) => handleChange(subpart.id, v == null ? '' : String(v))
                      : undefined
                  }
                />
              </>
            ) : subpart.is_interactive && subpart.interactive_html ? (
              <InteractiveWidget
                html={subpart.interactive_html}
                fallbackText={subpart.question_text}
                className="text-sm text-ink-800"
              />
            ) : subpart.question_text ? (
              <RichContent
                text={subpart.question_text}
                variant="block"
                className="text-sm text-ink-800"
              />
            ) : (
              <p className="text-sm text-ink-400 italic">No question text available.</p>
            )}

            {/*
              Answer-producing widgets (IW-4) are themselves the input — the
              student drags / clicks / selects inside the widget and that
              becomes the answer via onValue above. Rendering the typed
              SubpartInput too would put a confusing parallel field below the
              widget. Show a small post-grade summary instead so the student
              still sees what they submitted.
            */}
            {widgetProducesAnswer ? (
              isSubmitted && (
                <p className="text-xs text-ink-500 mt-1">
                  Submitted value: <span className="font-semibold text-ink-900">{value || '—'}</span>
                </p>
              )
            ) : (
              <SubpartInput
                subpart={subpart}
                widgetType={subpart.subpart_type || question.question_type}
                value={value}
                onChange={(val) => handleChange(subpart.id, val)}
                isSubmitted={isSubmitted}
              />
            )}

            {isAnswered && !isSubmitted && (
              <p className="text-xs text-emerald-700 mt-1">Answered</p>
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
