import { memo, useMemo } from 'react';
import clsx from 'clsx';
import 'katex/dist/katex.min.css';
import { renderRichContent } from './renderRichContent';

/**
 * Render question/option/solution content that may contain HTML and LaTeX.
 *
 * - HTML is sanitised via DOMPurify (allowlist).
 * - LaTeX is rendered with KaTeX. Inline `$…$` / `\(…\)`; block `$$…$$` / `\[…\]`.
 * - Output is memoised on `text`; subsequent renders are O(1).
 *
 * Used by `QuestionCard`, `SRSDrillPage` (via QuestionCard), and the teacher
 * authoring preview — so a student, an SRS reviewer, and an author all see the
 * same rendered output.
 */
export interface RichContentProps {
  /** Raw HTML+LaTeX from the API (Cabinet-imported content, AI hints, etc.). */
  text: string;
  /** Visual variant; defaults to inline-flow body text. */
  variant?: 'block' | 'inline';
  /** Extra wrapper classes (compose with token classes only — no raw hex). */
  className?: string;
}

const RichContentImpl = ({ text, variant = 'inline', className }: RichContentProps) => {
  const html = useMemo(() => renderRichContent(text), [text]);

  if (!html) return null;

  return (
    <div
      className={clsx(
        'prose-osh',
        variant === 'block' ? 'block' : 'inline-block align-baseline',
        className
      )}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export const RichContent = memo(RichContentImpl);
