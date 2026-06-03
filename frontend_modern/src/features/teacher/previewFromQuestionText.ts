/**
 * Build a teacher-friendly plain-text preview from a subpart's stored
 * question_text. Used by row-based question pickers (Build Problem Set,
 * Question Bank list) that render dozens of rows at once and can't afford to
 * mount a full `<RichContent>` per row (KaTeX × N is heavy and visually noisy
 * in a single-line row).
 *
 * Stripping rules (apply in order):
 *   1. LaTeX environments — `\begin{X}…\end{X}` → ` [math] `
 *   2. Block math — `$$…$$`, `\[…\]` → ` [math] `
 *   3. Inline math — `$…$`, `\(…\)` → ` [math] `
 *   4. `{{var}}` tokens — per-student values aren't picked yet → `?`
 *   5. All remaining HTML/SVG tags → space
 *   6. Common HTML entities decoded (`&nbsp;`, `&amp;`, `&lt;`, …)
 *   7. Whitespace collapsed, then truncated for the row
 *
 * Full rich rendering (HTML + KaTeX) happens elsewhere via `<RichContent>`
 * (assignment detail, SRS drill, Question Bank detail view).
 */
export const previewFromQuestionText = (raw: string | null | undefined): string => {
  if (!raw) return '(no text)';
  let text = raw;
  // LaTeX environments first (before tag-strip would mangle their braces).
  text = text.replace(/\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}/g, ' [math] ');
  // Block + inline math.
  text = text.replace(/\$\$[\s\S]*?\$\$/g, ' [math] ');
  text = text.replace(/\\\[[\s\S]*?\\\]/g, ' [math] ');
  text = text.replace(/\$[^$\n]+\$/g, ' [math] ');
  text = text.replace(/\\\([\s\S]*?\\\)/g, ' [math] ');
  // {{var}} tokens — substituted per student elsewhere; show "?" in pickers.
  text = text.replace(/\{\{[^{}]+\}\}/g, '?');
  // Strip every remaining HTML/SVG tag.
  text = text.replace(/<[^>]+>/g, ' ');
  // Decode the common HTML entities the cabinet content uses.
  text = text
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  // Collapse whitespace.
  text = text.replace(/\s+/g, ' ').trim();
  if (!text) return '(no text)';
  const MAX = 120;
  return text.length > MAX ? text.slice(0, MAX).trimEnd() + '…' : text;
};
