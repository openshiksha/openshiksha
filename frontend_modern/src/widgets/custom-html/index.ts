/**
 * `custom-html` — the **escape hatch** for genuinely-novel one-off
 * widgets that can't be expressed by the registry's first-party kinds
 * or the Tier-2 Studio's primitives.
 *
 * Purpose
 * -------
 * Pass an HTML string in `widget_config.html`; the widget renders it
 * inside the same sandboxed iframe every other widget uses. Inline
 * `<script>` tags are re-executed so authored interactivity actually
 * runs (a plain `innerHTML` assignment does *not* execute scripts).
 *
 * This kind is the final piece that lets us deprecate the
 * `QuestionSubpart.interactive_html` raw HTML field (M7-11). Once any
 * legacy raw-HTML question is migrated to
 * `widget_kind='custom-html' + widget_config={html: ...}`, every
 * authoring path on the platform — Tier-1 registry widget, Tier-2
 * Studio scene, Tier-3 contributor widget, *and* one-off bespoke HTML
 * — flows through the same `InteractiveWidget` host.
 *
 * Authoring scope
 * ---------------
 * **Admin-only.** Per the IW-7 spec, the teacher gallery (IW-5) must
 * filter this kind out so regular teachers cannot inject raw scripts;
 * only a school admin can attach a `custom-html` widget to a question.
 * `meta.title` carries the "(admin only)" affordance until the
 * gallery picker exists to enforce it programmatically.
 *
 * Vendor head
 * -----------
 * The framework runtime is React-only — no jQuery / Bootstrap. Legacy
 * Cabinet content that relies on those vendor libs can include them in
 * the HTML itself via `<script src="https://..."></script>`. The
 * script-re-execution path below handles both inline and `src`-style
 * tags, including load-order via `async = false`.
 */

import { defineWidget } from '../_sdk/defineWidget';
import paramsSchema from './params.schema.json';

interface CustomHtmlConfig {
  /** Raw HTML to render inside the sandbox. May contain `<script>` tags. */
  html?: string;
}

export default defineWidget({
  kind: 'custom-html',
  version: 1,
  meta: {
    title: 'Custom HTML (admin only)',
    description:
      'Render an arbitrary HTML snippet with inline scripts inside the same ' +
      'sandboxed iframe every widget uses. Use this only when no registered ' +
      'widget or Studio composition fits — every script you author here runs ' +
      'in an opaque-origin sandbox, but it is still your code shipping to students.',
    answerProducing: false,
  },
  paramsSchema,
  render: (ctx) => {
    const cfg = ctx.config as CustomHtmlConfig;
    const html = typeof cfg.html === 'string' ? cfg.html : '';

    if (!html) {
      const empty = document.createElement('p');
      empty.textContent = 'custom-html: no `html` field in widget_config.';
      empty.style.margin = '0';
      empty.style.color = '#9B1C1C';
      ctx.mount.appendChild(empty);
      return;
    }

    // Drop the raw HTML in. `innerHTML` parses scripts into DOM nodes
    // *but does not execute them* — every browser intentionally inerts
    // scripts inserted this way. Walk the inserted subtree and replace
    // each `<script>` with a freshly created node carrying the same
    // attributes; that triggers normal script execution.
    ctx.mount.innerHTML = html;

    // Re-execute scripts in their original document order. Cloning into
    // a fresh element + appending is the canonical pattern (browsers
    // queue these like any other parser-inserted script, including for
    // `src` fetches and load ordering).
    const scripts = Array.from(ctx.mount.querySelectorAll('script'));
    for (const old of scripts) {
      const fresh = document.createElement('script');
      // Preserve `type`, `src`, and any other attributes the author set.
      for (const attr of Array.from(old.attributes)) {
        fresh.setAttribute(attr.name, attr.value);
      }
      // For src-less inline scripts, copy the body text so it runs.
      if (!old.src && old.textContent) {
        fresh.textContent = old.textContent;
      }
      // `async = false` keeps multiple `src`-style scripts in document
      // order, matching how the legacy vendor head loaded jQuery before
      // jQuery-UI.
      if (old.src) fresh.async = false;
      old.parentNode?.replaceChild(fresh, old);
    }
  },
});
