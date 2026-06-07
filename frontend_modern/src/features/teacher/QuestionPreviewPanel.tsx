import { ReactNode } from 'react';
import { Badge, Card } from '@/shared/ui';
import { RichContent } from '@/shared/ui/RichContent';
import { difficultyStars, typeLabel, typeTone } from './questionPreviewMeta';
import type { MCQOption, Question, QuestionSubpart } from '@/types/index';

const optionLetter = (i: number) => String.fromCharCode(65 + i);

// ── Keyhole "empty preview" motif ───────────────────────────────────────────

const KeyholeEmpty = ({ title, description }: { title: string; description: string }) => (
  <Card className="flex h-full min-h-[24rem] flex-col items-center justify-center text-center">
    <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-50">
      <svg viewBox="0 0 64 64" className="h-9 w-9 text-brand-500" fill="none">
        <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="2" opacity="0.2" />
        <circle cx="32" cy="26" r="7" stroke="currentColor" strokeWidth="3" />
        <path
          d="M28 31 L26 44 L38 44 L36 31"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
    <h3 className="font-display text-lg font-semibold text-ink-900">{title}</h3>
    <p className="mt-1 max-w-sm text-sm text-ink-500">{description}</p>
  </Card>
);

// ── Subpart preview (used inside QuestionPreviewPanel) ──────────────────────

const SubpartPreview = ({
  subpart,
  index,
  total,
}: {
  subpart: QuestionSubpart;
  index: number;
  total: number;
}) => {
  const hasOptions = Array.isArray(subpart.options) && subpart.options.length > 0;
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-5 shadow-soft">
      {total > 1 && (
        <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-brand-600">
          Part {String.fromCharCode(97 + index)}
        </p>
      )}
      <div className="prose-osh text-ink-800">
        <RichContent text={subpart.question_text} variant="block" />
      </div>
      {subpart.image_url && (
        <img
          src={subpart.image_url}
          alt="Question diagram"
          className="mt-4 max-h-64 rounded-lg border border-ink-100 object-contain"
        />
      )}
      {hasOptions && (
        <ul className="mt-4 space-y-2">
          {(subpart.options as MCQOption[]).map((opt, i) => (
            <li
              key={opt.key ?? i}
              className="flex items-start gap-3 rounded-lg border border-ink-100 bg-paper px-3 py-2"
            >
              <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ink-100 text-xs font-semibold text-ink-700">
                {opt.key ?? optionLetter(i)}
              </span>
              <div className="prose-osh min-w-0 flex-1 text-sm text-ink-700">
                <RichContent text={opt.text ?? ''} />
              </div>
            </li>
          ))}
        </ul>
      )}
      {!hasOptions && subpart.subpart_type === 'numeric' && (
        <p className="mt-4 inline-flex items-center gap-2 rounded-lg border border-ink-100 bg-paper px-3 py-2 text-xs text-ink-500">
          <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="currentColor">
            <path d="M3 4h10v2H3zm0 6h10v2H3z" />
          </svg>
          Numeric answer
        </p>
      )}
      {!hasOptions && subpart.subpart_type === 'fill_blank' && (
        <p className="mt-4 text-xs text-ink-500">Fill-in-the-blank response.</p>
      )}
      {subpart.is_interactive && (
        <p className="mt-4 inline-flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-800">
          🧪 Sandboxed interactive widget (rendered for students)
        </p>
      )}
    </div>
  );
};

// ── Main panel ──────────────────────────────────────────────────────────────

interface QuestionPreviewPanelProps {
  question: Question | null;
  emptyTitle?: string;
  emptyDescription?: string;
  /** Footer slot; usually an action button (e.g. "Add to set"). */
  footer?: ReactNode;
}

/**
 * Live, fully-rendered preview of a question — exactly what students will see.
 * Used by `CreateProblemSetPage` and `QuestionBankPage` to give teachers a
 * trustworthy preview before they commit a question to an assignment.
 *
 * Uses `<RichContent>` for question_text, MCQ options, and stem text so HTML +
 * KaTeX render properly. Optional footer slot lets the host page attach an
 * action (Add to set / Remove / Edit).
 */
export const QuestionPreviewPanel = ({
  question,
  emptyTitle = 'Pick a question to preview',
  emptyDescription = 'Click any row on the left to see exactly how students will see it — full LaTeX, options, images, and all.',
  footer,
}: QuestionPreviewPanelProps) => {
  if (!question) {
    return <KeyholeEmpty title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <Card className="flex h-full min-h-[24rem] flex-col">
      {/* Header strip */}
      <div className="-m-6 mb-5 rounded-t-xl2 border-b border-ink-100 bg-paper px-6 py-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={typeTone(question.question_type)}>{typeLabel(question.question_type)}</Badge>
          <span
            className="text-sm tracking-wider text-amber-500"
            title={`Difficulty ${question.difficulty}/5`}
          >
            {difficultyStars(question.difficulty)}
          </span>
          {question.chapter_name && (
            <span className="text-xs text-ink-500">· {question.chapter_name}</span>
          )}
          {question.subject_name && (
            <span className="text-xs text-ink-500">· {question.subject_name}</span>
          )}
          <span className="ml-auto font-mono text-xs text-ink-400">#{question.id}</span>
        </div>
        {question.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {question.tags.slice(0, 6).map((t) => (
              <span
                key={t.id}
                className="rounded-md bg-ink-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ink-600"
              >
                {t.name}
              </span>
            ))}
            {question.tags.length > 6 && (
              <span className="text-[10px] text-ink-400">+{question.tags.length - 6}</span>
            )}
          </div>
        )}
      </div>

      {/* Body — stem + subparts */}
      <div className="-mb-2 max-h-[40rem] flex-1 space-y-4 overflow-y-auto pr-2">
        {question.stem_text && (
          <div className="prose-osh rounded-xl border border-ink-100 bg-brand-50/40 p-4 text-ink-700">
            <RichContent text={question.stem_text} variant="block" />
          </div>
        )}
        {question.subparts.map((sp, i) => (
          <SubpartPreview key={sp.id} subpart={sp} index={i} total={question.subparts.length} />
        ))}
      </div>

      {/* Optional footer */}
      {footer && (
        <div className="-mx-6 -mb-6 mt-5 flex items-center justify-between gap-3 rounded-b-xl2 border-t border-ink-100 bg-paper px-6 py-3">
          {footer}
        </div>
      )}
    </Card>
  );
};
