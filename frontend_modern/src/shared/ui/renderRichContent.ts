import createDOMPurify from 'dompurify';
import type Katex from 'katex';

// KaTeX is the largest single dependency in the bundle (~257 kB / ~77 kB gzip).
// We dynamic-import it from `<RichContent>` only when the text actually contains
// math delimiters, so dashboards / browse pages / non-math content never pay for
// it on first paint. The component pokes the loaded module in here via
// `setKatex()`; until that happens (or for non-math content) `renderRichContent`
// is fully usable and just renders math expressions as escaped fallback text.
//
// In Vitest, `src/test-setup.ts` preloads KaTeX synchronously so the existing
// sync renderer tests don't have to become async.
let katexRef: typeof Katex | null = null;
export function setKatex(mod: typeof Katex): void {
  katexRef = mod;
}
export function isKatexLoaded(): boolean {
  return katexRef !== null;
}

// Cheap pre-check so `<RichContent>` can decide whether to even kick off the
// dynamic import. Matches the same delimiters the renderer recognises.
const MATH_HINT_PATTERN = /\$|\\\(|\\\[|\\begin\{/;
export function textContainsMath(text: string): boolean {
  return MATH_HINT_PATTERN.test(text);
}

/**
 * Pure HTML+LaTeX renderer used by `<RichContent />`. Split into its own file
 * so the component module can stay fast-refresh-friendly (component-only export).
 *
 * - Sanitises raw HTML via DOMPurify (allowlist below).
 * - Replaces LaTeX delimiters (`$…$`, `\(…\)`, `$$…$$`, `\[…\]`) with KaTeX HTML.
 */

const ALLOWED_TAGS = [
  'p', 'br', 'span', 'div',
  'strong', 'em', 'b', 'i', 'u',
  'sup', 'sub', 'small',
  'ul', 'ol', 'li',
  'code', 'pre',
  'img',
  'table', 'thead', 'tbody', 'tr', 'td', 'th',
  'a',
];

const ALLOWED_ATTR = ['href', 'src', 'alt', 'width', 'height', 'title', 'class', 'colspan', 'rowspan'];

// M7-06: only http(s) image sources survive. Cabinet inline `<img>` paths are
// rewritten to absolute raw.githubusercontent.com URLs at import time, so any
// non-http(s) `src` (relative leftovers, `data:` SVG payloads, `javascript:`)
// is an XSS vector or a guaranteed broken image — drop the attribute entirely.
const HTTP_SRC = /^https?:\/\//i;
const DOMPurify = createDOMPurify(window);
const FORBIDDEN_CONTENT_SELECTOR = 'script, style, iframe, object, embed';

// `exprGroup: 0` means feed the entire match to KaTeX (used for un-delimited
// `\begin{X}…\end{X}` environments where the begin/end tokens are part of the
// LaTeX source). `exprGroup: 1` strips the surrounding delimiter.
const DELIMITERS: Array<{ re: RegExp; block: boolean; exprGroup: 0 | 1 }> = [
  // Un-delimited LaTeX environments — listed first so an env embedded in a
  // paragraph wins over any inner `$…$` partial matches.
  // Non-greedy `[\s\S]*?` + back-reference to the opening name; Cabinet
  // environments don't nest so this is safe across the corpus.
  { re: /\\begin\{([a-zA-Z*]+)\}[\s\S]*?\\end\{\1\}/g, block: true, exprGroup: 0 },
  { re: /\$\$([\s\S]+?)\$\$/g, block: true, exprGroup: 1 },
  { re: /\\\[([\s\S]+?)\\\]/g, block: true, exprGroup: 1 },
  { re: /\\\(([\s\S]+?)\\\)/g, block: false, exprGroup: 1 },
  { re: /(?<!\$)\$([^$\n]+?)\$(?!\$)/g, block: false, exprGroup: 1 },
];

interface MathHit {
  start: number;
  end: number;
  expr: string;
  block: boolean;
}

function findMath(source: string): MathHit[] {
  const hits: MathHit[] = [];
  for (const { re, block, exprGroup } of DELIMITERS) {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(source)) !== null) {
      const expr = exprGroup === 0 ? m[0] : m[1];
      hits.push({ start: m.index, end: m.index + m[0].length, expr, block });
    }
  }
  hits.sort((a, b) => a.start - b.start);
  const merged: MathHit[] = [];
  let cursor = -1;
  for (const h of hits) {
    if (h.start >= cursor) {
      merged.push(h);
      cursor = h.end;
    }
  }
  return merged;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderKatex(expr: string, block: boolean): string {
  if (!katexRef) {
    // Fallback before the lazy KaTeX chunk has finished loading. We render the
    // raw expression as inline-code so the user sees something readable rather
    // than a blank flash; the component re-renders once KaTeX is ready.
    const tag = block ? 'div' : 'span';
    return `<${tag} class="katex-pending font-mono text-ink-700">${escapeHtml(expr)}</${tag}>`;
  }
  try {
    return katexRef.renderToString(expr, {
      throwOnError: false,
      displayMode: block,
      strict: 'ignore',
      output: 'html',
    });
  } catch {
    return `<span class="text-rose-700 underline decoration-rose-400 decoration-dotted">${escapeHtml(expr)}</span>`;
  }
}

function dropForbiddenContent(text: string): string {
  const template = document.createElement('template');
  template.innerHTML = text;
  template.content.querySelectorAll(FORBIDDEN_CONTENT_SELECTOR).forEach((node) => node.remove());
  return template.innerHTML;
}

function dropUnsafeImageSources(fragment: DocumentFragment): void {
  fragment.querySelectorAll('img[src]').forEach((img) => {
    const src = img.getAttribute('src') ?? '';
    if (!HTTP_SRC.test(src)) img.removeAttribute('src');
  });
}

function injectMath(fragment: DocumentFragment): string {
  const walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT);
  const replacements: Array<{ node: Text; html: string }> = [];

  let node: Node | null = walker.nextNode();
  while (node) {
    const textNode = node as Text;
    const value = textNode.nodeValue ?? '';
    const hits = findMath(value);
    if (hits.length > 0) {
      let out = '';
      let cursor = 0;
      for (const hit of hits) {
        if (hit.start > cursor) out += escapeHtml(value.slice(cursor, hit.start));
        out += renderKatex(hit.expr, hit.block);
        cursor = hit.end;
      }
      if (cursor < value.length) out += escapeHtml(value.slice(cursor));
      replacements.push({ node: textNode, html: out });
    }
    node = walker.nextNode();
  }

  for (const { node: textNode, html } of replacements) {
    const span = document.createElement('span');
    span.innerHTML = html;
    textNode.parentNode?.replaceChild(span, textNode);
  }

  const wrapper = document.createElement('div');
  wrapper.appendChild(fragment);
  return wrapper.innerHTML;
}

export function renderRichContent(text: string): string {
  if (!text) return '';

  const cleanHtml = DOMPurify.sanitize(`<div>${dropForbiddenContent(text)}</div>`, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick'],
  });

  const template = document.createElement('template');
  template.innerHTML = cleanHtml;
  dropUnsafeImageSources(template.content);
  return injectMath(template.content);
}
