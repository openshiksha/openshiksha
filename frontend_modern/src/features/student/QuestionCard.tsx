import { useCallback } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import type { Question, QuestionSubpart, MCQOption } from '@/types/index';

interface QuestionCardProps {
  question: Question;
  questionNumber: number;
  answers: Record<string, string>;
  onAnswerChange: (subpartId: number, value: string) => void;
  isSubmitted: boolean;
}

/**
 * Render mixed LaTeX/plain-text content.
 * Supports $$...$$ (block math) and $...$ (inline math) delimiters.
 */
function renderMixedContent(text: string): React.ReactNode[] {
  if (!text) return [];

  const nodes: React.ReactNode[] = [];
  // Match $$...$$ first (block), then $...$ (inline)
  const pattern = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    // Plain text before this match
    if (match.index > lastIndex) {
      nodes.push(
        <span key={`text-${lastIndex}`}>{text.slice(lastIndex, match.index)}</span>
      );
    }

    const raw = match[0];
    const isBlock = raw.startsWith('$$');
    const expr = isBlock ? raw.slice(2, -2) : raw.slice(1, -1);

    try {
      const html = katex.renderToString(expr, {
        throwOnError: false,
        displayMode: isBlock,
      });
      nodes.push(
        <span
          key={`math-${match.index}`}
          dangerouslySetInnerHTML={{ __html: html }}
          className={isBlock ? 'block my-2' : 'inline'}
        />
      );
    } catch {
      nodes.push(<span key={`math-${match.index}`}>{raw}</span>);
    }

    lastIndex = match.index + raw.length;
  }

  // Remaining plain text
  if (lastIndex < text.length) {
    nodes.push(<span key={`text-end`}>{text.slice(lastIndex)}</span>);
  }

  return nodes;
}

interface SubpartInputProps {
  subpart: QuestionSubpart;
  questionType: Question['question_type'];
  value: string;
  onChange: (value: string) => void;
  isSubmitted: boolean;
}

function SubpartInput({ subpart, questionType, value, onChange, isSubmitted }: SubpartInputProps) {
  if (questionType === 'mcq' && subpart.options) {
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
              {renderMixedContent(opt.text)}
            </span>
          </label>
        ))}
      </div>
    );
  }

  if (questionType === 'multi_select' && subpart.options) {
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
              {renderMixedContent(opt.text)}
            </span>
          </label>
        ))}
      </div>
    );
  }

  if (questionType === 'numeric') {
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

      {question.subparts.map((subpart, i) => {
        const value = answers[String(subpart.id)] ?? '';
        const isAnswered = value.trim().length > 0;

        return (
          <div key={subpart.id} className={i > 0 ? 'mt-6 pt-6 border-t border-gray-100' : ''}>
            {question.subparts.length > 1 && (
              <p className="text-xs text-gray-400 mb-1">Part {String.fromCharCode(97 + i)})</p>
            )}

            {subpart.question_text ? (
              <div className="text-sm text-gray-800 leading-relaxed">
                {renderMixedContent(subpart.question_text)}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">No question text available.</p>
            )}

            <SubpartInput
              subpart={subpart}
              questionType={question.question_type}
              value={value}
              onChange={(val) => handleChange(subpart.id, val)}
              isSubmitted={isSubmitted}
            />

            {isAnswered && !isSubmitted && (
              <p className="text-xs text-green-600 mt-1">Answered</p>
            )}
          </div>
        );
      })}
    </div>
  );
};
