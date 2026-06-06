/**
 * `fraction-bar` — an **explanatory** primary-school widget (IW-6) that
 * shows a fraction `numerator / denominator` as a horizontal bar split
 * into equal segments with the filled portion highlighted. Great for
 * "what fraction of the bar is shaded?" style questions and for
 * building intuition about equivalent fractions.
 *
 * Two render modes
 * ----------------
 * - **`shaded`** (default): bar is split into `denominator` equal
 *   segments, the first `numerator` are filled in brand orange. The
 *   teacher's question typically asks the student to *name* the
 *   fraction; the widget itself doesn't display the numerals so the
 *   answer isn't given away.
 * - **`labelled`**: same bar plus a small `n / d` caption under it.
 *   Used in worked-solution / hint contexts where the teacher wants
 *   the value visible.
 *
 * No `reportValue` — the student answers in the usual field below.
 */

import { defineWidget } from '../_sdk/defineWidget';
import paramsSchema from './params.schema.json';

interface FractionBarConfig {
  /** Top of the fraction. Default 1. Clamped to [0, denominator]. */
  numerator?: number;
  /** Bottom of the fraction. Must be a positive integer. Default 4. */
  denominator?: number;
  /** `"shaded"` (default) hides numerals; `"labelled"` shows them. */
  mode?: 'shaded' | 'labelled';
  /** Optional title shown above the bar. */
  title?: string;
}

export default defineWidget({
  kind: 'fraction-bar',
  version: 1,
  meta: {
    title: 'Fraction bar',
    description: 'Shaded bar showing numerator / denominator. Explanatory; great for primary-school fractions.',
    answerProducing: false,
  },
  paramsSchema,
  render: (ctx) => {
    const cfg = ctx.config as FractionBarConfig;
    // Clamp to sane bounds. A denominator of 0 would be a division by
    // zero in the math the question is teaching, but here it'd just
    // be an empty bar — treat it as "1" so the widget always shows
    // something.
    const rawDen = Number.isFinite(cfg.denominator) ? Math.round(cfg.denominator as number) : 4;
    const denominator = Math.max(1, Math.min(40, rawDen));
    const rawNum = Number.isFinite(cfg.numerator) ? Math.round(cfg.numerator as number) : 1;
    const numerator = Math.max(0, Math.min(denominator, rawNum));
    const mode: 'shaded' | 'labelled' = cfg.mode === 'labelled' ? 'labelled' : 'shaded';
    const title = typeof cfg.title === 'string' ? cfg.title : '';

    const style = document.createElement('style');
    style.textContent = `
      .fb-root { display: grid; gap: 6px; }
      .fb-title { font-family: "Fraunces", Georgia, serif; font-size: 15px; font-weight: 600; margin: 0; }
      .fb-caption { font-family: "Fraunces", Georgia, serif; font-size: 18px; color: #1B1A17; margin: 4px 0 0 0; }
      .fb-caption sup, .fb-caption sub { font-size: 14px; }
      .fb-hint { font-size: 12px; color: #6B6357; margin: 0; }
    `;
    ctx.mount.appendChild(style);

    const root = document.createElement('div');
    root.className = 'fb-root';
    ctx.mount.appendChild(root);

    if (title) {
      const t = document.createElement('p');
      t.className = 'fb-title';
      t.textContent = title;
      root.appendChild(t);
    }

    // SVG bar — width fills the host, height is fixed so 40-segment bars
    // still render with visible separators.
    const SVG_NS = 'http://www.w3.org/2000/svg';
    const W = 400;
    const H = 60;
    const PAD = 6;
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', String(H));
    svg.setAttribute(
      'aria-label',
      'Fraction bar showing ' + numerator + ' of ' + denominator + ' parts shaded',
    );
    root.appendChild(svg);

    const segW = (W - PAD * 2) / denominator;
    for (let i = 0; i < denominator; i++) {
      const seg = document.createElementNS(SVG_NS, 'rect');
      seg.setAttribute('x', String(PAD + i * segW));
      seg.setAttribute('y', String(PAD));
      seg.setAttribute('width', String(segW));
      seg.setAttribute('height', String(H - PAD * 2));
      seg.setAttribute('fill', i < numerator ? '#FF6F00' : '#FBF7EE');
      seg.setAttribute('stroke', '#1B1A17');
      seg.setAttribute('stroke-width', '1.5');
      svg.appendChild(seg);
    }

    if (mode === 'labelled') {
      const caption = document.createElement('p');
      caption.className = 'fb-caption';
      caption.innerHTML =
        '<sup>' + String(numerator) + '</sup>&frasl;<sub>' + String(denominator) + '</sub>';
      root.appendChild(caption);
    } else {
      const hint = document.createElement('p');
      hint.className = 'fb-hint';
      hint.textContent = 'What fraction of the bar is shaded?';
      root.appendChild(hint);
    }
  },
});
