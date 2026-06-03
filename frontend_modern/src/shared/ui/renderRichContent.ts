import DOMPurify from 'dompurify';
import katex from 'katex';

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
// Registered once at module load; DOMPurify hooks are process-global.
const HTTP_SRC = /^https?:\/\//i;
let imgSrcHookRegistered = false;
function ensureImgSrcHook(): void {
  if (imgSrcHookRegistered) return;
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.nodeName === 'IMG' && node.hasAttribute('src')) {
      const src = node.getAttribute('src') ?? '';
      if (!HTTP_SRC.test(src)) node.removeAttribute('src');
    }
  });
  imgSrcHookRegistered = true;
}

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
  try {
    return katex.renderToString(expr, {
      throwOnError: false,
      displayMode: block,
      strict: 'ignore',
      output: 'html',
    });
  } catch {
    return `<span class="text-rose-700 underline decoration-rose-400 decoration-dotted">${escapeHtml(expr)}</span>`;
  }
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

  ensureImgSrcHook();
  const cleanHtml = DOMPurify.sanitize(text, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick'],
  });

  const template = document.createElement('template');
  template.innerHTML = cleanHtml;
  return injectMath(template.content);
}
