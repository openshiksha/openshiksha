/**
 * `number-line` — the framework's **first answer-producing widget** (IW-4).
 *
 * The student drags a point along a labelled axis; the position (snapped
 * to `step`) becomes their answer via `ctx.reportValue(value)`. The host
 * routes that value into the question's submission form, where the
 * existing numeric grader marks it correct/incorrect against
 * `correct_answer` — no parallel grader code path.
 *
 * Design notes
 * ------------
 * - **Pointer events**, not mouse events, so the same drag handler
 *   covers mouse, touch, and stylus without three code paths.
 * - **`pointercapture`** so a drag that leaves the iframe body still
 *   fires moves until release — the legacy widgets had to track
 *   `mouseup` on `window` to handle this; we get it for free.
 * - **Snap to `step` on every move**, not just on release, so the
 *   reported value matches what the student sees under the point at
 *   all times. The grader receives whatever the student last saw.
 * - **No `reportValue` on mount.** The widget only reports a value
 *   after the student actually interacts — otherwise the answer form
 *   would be pre-filled with the initial position and the student
 *   couldn't leave a question blank.
 */

import { defineWidget } from '../_sdk/defineWidget';
import paramsSchema from './params.schema.json';

interface NumberLineConfig {
  /** Left-end value on the axis (default 0). */
  min?: number;
  /** Right-end value on the axis (default 10). */
  max?: number;
  /** Snap step (default 1). Must be > 0. */
  step?: number;
  /** Where the point starts before the student drags (default `min`). */
  initial?: number;
  /** Optional label rendered above the axis. */
  label?: string;
}

export default defineWidget({
  kind: 'number-line',
  version: 1,
  meta: {
    title: 'Number line',
    description: 'Drag a point along a labelled number line; the value becomes the answer.',
    answerProducing: true,
  },
  paramsSchema,
  render: (ctx) => {
    const cfg = ctx.config as NumberLineConfig;
    const min = Number.isFinite(cfg.min) ? (cfg.min as number) : 0;
    const max = Number.isFinite(cfg.max) ? (cfg.max as number) : 10;
    const step = Number.isFinite(cfg.step) && (cfg.step as number) > 0 ? (cfg.step as number) : 1;
    const initial = Number.isFinite(cfg.initial) ? (cfg.initial as number) : min;
    const label = typeof cfg.label === 'string' ? cfg.label : '';

    // SVG geometry. The axis spans X=40..360 inside a 400-wide viewBox
    // so labels at the ends have a little margin against the iframe wall.
    const SVG_NS = 'http://www.w3.org/2000/svg';
    const AXIS_X0 = 40;
    const AXIS_X1 = 360;
    const AXIS_Y = 60;
    const AXIS_LEN = AXIS_X1 - AXIS_X0;
    const range = max - min;

    function valueToX(v: number): number {
      if (range === 0) return AXIS_X0;
      return AXIS_X0 + ((v - min) / range) * AXIS_LEN;
    }
    function xToValue(x: number): number {
      if (range === 0) return min;
      const clamped = Math.max(AXIS_X0, Math.min(AXIS_X1, x));
      return min + ((clamped - AXIS_X0) / AXIS_LEN) * range;
    }
    function snap(v: number): number {
      const snapped = Math.round((v - min) / step) * step + min;
      const clamped = Math.max(min, Math.min(max, snapped));
      // Round to a small number of decimals so a step of 0.1 doesn't end
      // up reporting `0.30000000000000004`.
      const decimals = Math.max(0, -Math.floor(Math.log10(step)));
      return Number(clamped.toFixed(decimals));
    }

    // Style block scoped to the widget root. Brand tokens (#FF6F00 anchor)
    // come from the runtime body styles; we only set rules specific to
    // this widget's interactive surface.
    const style = document.createElement('style');
    style.textContent = `
      .nl-root { display: grid; gap: 8px; user-select: none; }
      .nl-label { font-size: 14px; font-weight: 600; margin: 0; }
      .nl-readout { font-size: 14px; margin: 0; color: #4B463E; }
      .nl-readout strong { color: #1B1A17; font-size: 16px; }
      .nl-hint { font-size: 12px; color: #6B6357; margin: 0; }
      .nl-svg { touch-action: none; cursor: grab; }
      .nl-svg:active { cursor: grabbing; }
      .nl-point { transition: r 80ms ease-out; }
      .nl-point:hover { r: 11; }
    `;
    ctx.mount.appendChild(style);

    const root = document.createElement('div');
    root.className = 'nl-root';
    ctx.mount.appendChild(root);

    if (label) {
      const labelEl = document.createElement('p');
      labelEl.className = 'nl-label';
      labelEl.textContent = label;
      root.appendChild(labelEl);
    }

    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 400 110');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '110');
    svg.setAttribute('class', 'nl-svg');
    svg.setAttribute('role', 'slider');
    svg.setAttribute('aria-valuemin', String(min));
    svg.setAttribute('aria-valuemax', String(max));
    svg.setAttribute('aria-label', label || 'Number line');
    root.appendChild(svg);

    // Axis line.
    const axis = document.createElementNS(SVG_NS, 'line');
    axis.setAttribute('x1', String(AXIS_X0));
    axis.setAttribute('x2', String(AXIS_X1));
    axis.setAttribute('y1', String(AXIS_Y));
    axis.setAttribute('y2', String(AXIS_Y));
    axis.setAttribute('stroke', '#1B1A17');
    axis.setAttribute('stroke-width', '2');
    svg.appendChild(axis);

    // Ticks + labels. If `range / step` is huge we cap to ~12 visible
    // tick labels so an axis like 0..1000 step 1 doesn't draw 1000 text
    // nodes — but the snap still uses the real step.
    const totalTicks = range / step;
    const labelEvery = totalTicks > 12 ? Math.ceil(totalTicks / 12) : 1;
    for (let i = 0; i <= totalTicks; i++) {
      const v = min + i * step;
      const x = valueToX(v);
      const tick = document.createElementNS(SVG_NS, 'line');
      tick.setAttribute('x1', String(x));
      tick.setAttribute('x2', String(x));
      tick.setAttribute('y1', String(AXIS_Y - 6));
      tick.setAttribute('y2', String(AXIS_Y + 6));
      tick.setAttribute('stroke', '#1B1A17');
      tick.setAttribute('stroke-width', '1.5');
      svg.appendChild(tick);
      if (i % labelEvery === 0 || i === totalTicks) {
        const text = document.createElementNS(SVG_NS, 'text');
        text.setAttribute('x', String(x));
        text.setAttribute('y', String(AXIS_Y + 26));
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '12');
        text.setAttribute('fill', '#4B463E');
        text.textContent = String(v);
        svg.appendChild(text);
      }
    }

    // Draggable point.
    const point = document.createElementNS(SVG_NS, 'circle');
    point.setAttribute('cx', String(valueToX(snap(initial))));
    point.setAttribute('cy', String(AXIS_Y));
    point.setAttribute('r', '9');
    point.setAttribute('fill', '#FF6F00');
    point.setAttribute('stroke', '#1B1A17');
    point.setAttribute('stroke-width', '1.5');
    point.setAttribute('class', 'nl-point');
    svg.appendChild(point);

    // Live readout.
    const readout = document.createElement('p');
    readout.className = 'nl-readout';
    readout.innerHTML = 'Your answer: <strong>—</strong>';
    root.appendChild(readout);

    const hint = document.createElement('p');
    hint.className = 'nl-hint';
    hint.textContent = 'Drag the point along the line to choose a value.';
    root.appendChild(hint);

    let currentValue = snap(initial);
    let hasInteracted = false;

    function paint(v: number) {
      currentValue = v;
      point.setAttribute('cx', String(valueToX(v)));
      svg.setAttribute('aria-valuenow', String(v));
      const strong = readout.querySelector('strong');
      if (strong) strong.textContent = hasInteracted ? String(v) : '—';
    }
    paint(currentValue);

    // Convert a client-pixel event into the SVG's internal coordinate
    // system so the point follows the cursor regardless of CSS sizing.
    function clientXToSvgX(clientX: number): number {
      const rect = svg.getBoundingClientRect();
      const scale = 400 / rect.width;
      return (clientX - rect.left) * scale;
    }

    function applyFromPointer(ev: PointerEvent) {
      const v = snap(xToValue(clientXToSvgX(ev.clientX)));
      if (!hasInteracted || v !== currentValue) {
        hasInteracted = true;
        paint(v);
        ctx.reportValue(v);
      }
    }

    svg.addEventListener('pointerdown', (ev) => {
      // pointercapture means subsequent moves fire on the SVG even if
      // the cursor leaves the body — no need to attach window listeners.
      svg.setPointerCapture(ev.pointerId);
      applyFromPointer(ev);
    });
    svg.addEventListener('pointermove', (ev) => {
      if (svg.hasPointerCapture(ev.pointerId)) {
        applyFromPointer(ev);
      }
    });
    svg.addEventListener('pointerup', (ev) => {
      if (svg.hasPointerCapture(ev.pointerId)) {
        svg.releasePointerCapture(ev.pointerId);
      }
    });

    // Keyboard accessibility — arrow keys / Home / End nudge the point.
    svg.setAttribute('tabindex', '0');
    svg.addEventListener('keydown', (ev) => {
      let next: number;
      if (ev.key === 'ArrowLeft' || ev.key === 'ArrowDown') next = currentValue - step;
      else if (ev.key === 'ArrowRight' || ev.key === 'ArrowUp') next = currentValue + step;
      else if (ev.key === 'Home') next = min;
      else if (ev.key === 'End') next = max;
      else return;
      ev.preventDefault();
      const snapped = snap(next);
      hasInteracted = true;
      paint(snapped);
      ctx.reportValue(snapped);
    });
  },
});
