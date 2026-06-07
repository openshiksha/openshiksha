import { memo, useEffect, useMemo, useState } from 'react';
import clsx from 'clsx';
import {
  isKatexLoaded,
  renderRichContent,
  setKatex,
  textContainsMath,
} from './renderRichContent';

/**
 * Render question/option/solution content that may contain HTML and LaTeX.
 *
 * - HTML is sanitised via DOMPurify (allowlist).
 * - LaTeX is rendered with KaTeX. Inline `$…$` / `\(…\)`; block `$$…$$` / `\[…\]`.
 * - **KaTeX is dynamically imported only when the text actually contains math
 *   delimiters.** Non-math content (dashboards, browse tiles, options without
 *   formulas) never pays for the ~257 kB KaTeX chunk on first paint.
 * - Output is memoised on `text`; subsequent renders are O(1) until KaTeX
 *   finishes loading, at which point the component re-renders once with proper
 *   math glyphs in place of the pending fallback.
 */
export interface RichContentProps {
  /** Raw HTML+LaTeX from the API (Cabinet-imported content, AI hints, etc.). */
  text: string;
  /** Visual variant; defaults to inline-flow body text. */
  variant?: 'block' | 'inline';
  /** Extra wrapper classes (compose with token classes only — no raw hex). */
  className?: string;
}

let katexLoadPromise: Promise<void> | null = null;

function loadKatex(): Promise<void> {
  if (katexLoadPromise) return katexLoadPromise;
  katexLoadPromise = Promise.all([
    import('katex'),
    import('katex/dist/katex.min.css'),
  ]).then(([mod]) => {
    type KatexModule = typeof import('katex');
    const m = mod as unknown as { default?: KatexModule };
    setKatex(m.default ?? (mod as unknown as KatexModule));
  });
  return katexLoadPromise;
}

const RichContentImpl = ({ text, variant = 'inline', className }: RichContentProps) => {
  const hasMath = useMemo(() => textContainsMath(text), [text]);
  const [katexReady, setKatexReady] = useState(isKatexLoaded);

  useEffect(() => {
    if (!hasMath || katexReady) return;
    let cancelled = false;
    loadKatex().then(() => {
      if (!cancelled) setKatexReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, [hasMath, katexReady]);

  // `katexReady` participates in the memo key so the renderer re-runs once
  // KaTeX is available and the pending fallback is replaced with rendered math.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const html = useMemo(() => renderRichContent(text), [text, katexReady]);

  if (!html) return null;

  return (
    <div
      className={clsx(
        'prose-osh',
        variant === 'block' ? 'block' : 'inline-block align-baseline',
        className,
      )}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export const RichContent = memo(RichContentImpl);
