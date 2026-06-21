/**
 * `function-plotter` — an **explanatory** math widget (IW-6) that plots
 * `y = f(x)` over a configurable domain inside an SVG axis. The teacher
 * authors `expr` (e.g. `x**2 - 2*x + 1`); the widget samples it across
 * `xMin..xMax` and draws the curve. Useful for "look at the graph below
 * and answer..." style questions.
 *
 * Why not a JS `Function(expr)`?
 * ------------------------------
 * The render function runs inside the sandboxed iframe, which means the
 * sandbox boundary is what protects the host. But `Function()` and
 * `eval()` are noisy patterns that we'd rather not normalise in widget
 * source — a contributor copy-pasting from this widget would carry the
 * bad pattern forward. So the plotter ships a tiny recursive-descent
 * evaluator handling only the math the curriculum needs: numbers,
 * identifiers (`x`, `pi`, `e`), `+`, `-`, `*`, `/`, `**`, unary minus,
 * function calls (`sin`, `cos`, `tan`, `log`, `ln`, `exp`, `sqrt`,
 * `abs`, `pow`, `min`, `max`), and parentheses. Anything else throws
 * and the widget renders a friendly error band.
 *
 * Explanatory only — `reportValue` is never called; the answer field
 * below the widget collects the student's numeric / MCQ answer.
 */

import { defineWidget } from '../_sdk/defineWidget';
import paramsSchema from './params.schema.json';

interface FunctionPlotterConfig {
  /** Math expression in `x` to plot. Default `x**2`. */
  expr?: string;
  /** Left bound of the x-axis. Default −5. */
  xMin?: number;
  /** Right bound of the x-axis. Default +5. */
  xMax?: number;
  /** Bottom bound of the y-axis. Default −5. */
  yMin?: number;
  /** Top bound of the y-axis. Default +5. */
  yMax?: number;
  /** Optional title shown above the plot. */
  title?: string;
}

export default defineWidget({
  kind: 'function-plotter',
  version: 1,
  meta: {
    title: 'Function plotter',
    description: 'Plot a math expression in x over a configurable domain (safe-eval inside the sandbox).',
    answerProducing: false,
  },
  paramsSchema,
  render: (ctx) => {
    const cfg = ctx.config as FunctionPlotterConfig;
    const expr = typeof cfg.expr === 'string' && cfg.expr.trim() ? cfg.expr : 'x**2';
    const xMin = Number.isFinite(cfg.xMin) ? (cfg.xMin as number) : -5;
    const xMax = Number.isFinite(cfg.xMax) ? (cfg.xMax as number) : 5;
    const yMin = Number.isFinite(cfg.yMin) ? (cfg.yMin as number) : -5;
    const yMax = Number.isFinite(cfg.yMax) ? (cfg.yMax as number) : 5;
    const title = typeof cfg.title === 'string' ? cfg.title : '';

    const CONSTS: Record<string, number> = { pi: Math.PI, e: Math.E };
    const UNARY: Record<string, (n: number) => number> = {
      sin: Math.sin, cos: Math.cos, tan: Math.tan,
      asin: Math.asin, acos: Math.acos, atan: Math.atan,
      log: Math.log, ln: Math.log, log10: Math.log10,
      exp: Math.exp, sqrt: Math.sqrt, abs: Math.abs,
      floor: Math.floor, ceil: Math.ceil, round: Math.round,
    };
    const BINARY: Record<string, (a: number, b: number) => number> = {
      pow: Math.pow, min: Math.min, max: Math.max,
    };

    type Tok =
      | { t: 'num'; v: number }
      | { t: 'name'; v: string }
      | { t: 'op'; v: string }
      | { t: 'lp' } | { t: 'rp' } | { t: 'comma' };

    function tokenise(src: string): Tok[] {
      const out: Tok[] = [];
      let i = 0;
      while (i < src.length) {
        const c = src[i];
        if (/\s/.test(c)) { i++; continue; }
        if (c >= '0' && c <= '9') {
          let j = i + 1;
          while (j < src.length && /[0-9.]/.test(src[j])) j++;
          out.push({ t: 'num', v: Number(src.slice(i, j)) });
          i = j; continue;
        }
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c === '_') {
          let j = i + 1;
          while (j < src.length && /[A-Za-z0-9_]/.test(src[j])) j++;
          out.push({ t: 'name', v: src.slice(i, j) });
          i = j; continue;
        }
        if (c === '(') { out.push({ t: 'lp' }); i++; continue; }
        if (c === ')') { out.push({ t: 'rp' }); i++; continue; }
        if (c === ',') { out.push({ t: 'comma' }); i++; continue; }
        if (c === '*' && src[i + 1] === '*') { out.push({ t: 'op', v: '**' }); i += 2; continue; }
        if ('+-*/^'.includes(c)) { out.push({ t: 'op', v: c === '^' ? '**' : c }); i++; continue; }
        throw new Error('unexpected character: ' + c);
      }
      return out;
    }

    function compile(src: string): (x: number) => number {
      const toks = tokenise(src);
      let pos = 0;
      // Cache the result so TypeScript can narrow the discriminated union
      // through `t === 'op'` checks. Calling peek() repeatedly returns the
      // same value but with a wider inferred type each time.
      const peekOp = (): string | null => {
        const tok = toks[pos];
        return tok && tok.t === 'op' ? tok.v : null;
      };

      function parseAdd(): (x: number) => number {
        let left = parseMul();
        let op = peekOp();
        while (op === '+' || op === '-') {
          pos++;
          const right = parseMul();
          const l = left, r = right, o = op;
          left = (x) => (o === '+' ? l(x) + r(x) : l(x) - r(x));
          op = peekOp();
        }
        return left;
      }
      function parseMul(): (x: number) => number {
        let left = parsePow();
        let op = peekOp();
        while (op === '*' || op === '/') {
          pos++;
          const right = parsePow();
          const l = left, r = right, o = op;
          left = (x) => (o === '*' ? l(x) * r(x) : l(x) / r(x));
          op = peekOp();
        }
        return left;
      }
      function parsePow(): (x: number) => number {
        const base = parseUnary();
        if (peekOp() === '**') {
          pos++;
          const ex = parsePow(); // right-assoc
          return (x) => Math.pow(base(x), ex(x));
        }
        return base;
      }
      function parseUnary(): (x: number) => number {
        const op = peekOp();
        if (op === '-') {
          pos++;
          const inner = parseUnary();
          return (x) => -inner(x);
        }
        if (op === '+') { pos++; return parseUnary(); }
        return parseAtom();
      }
      function parseAtom(): (x: number) => number {
        const tok = toks[pos];
        if (!tok) throw new Error('unexpected end of expression');
        if (tok.t === 'num') { pos++; const v = tok.v; return () => v; }
        if (tok.t === 'lp') {
          pos++;
          const inner = parseAdd();
          const close = toks[pos];
          if (!close || close.t !== 'rp') throw new Error('missing )');
          pos++;
          return inner;
        }
        if (tok.t === 'name') {
          pos++;
          const name = tok.v;
          const after = toks[pos];
          if (after && after.t === 'lp') {
            pos++;
            const args: ((x: number) => number)[] = [];
            const first = toks[pos];
            if (!(first && first.t === 'rp')) {
              args.push(parseAdd());
              let nxt = toks[pos];
              while (nxt && nxt.t === 'comma') { pos++; args.push(parseAdd()); nxt = toks[pos]; }
            }
            const closeFn = toks[pos];
            if (!closeFn || closeFn.t !== 'rp') throw new Error('missing )');
            pos++;
            if (args.length === 1 && UNARY[name]) {
              const f = UNARY[name]; const a = args[0];
              return (x) => f(a(x));
            }
            if (args.length === 2 && BINARY[name]) {
              const f = BINARY[name]; const a = args[0]; const b = args[1];
              return (x) => f(a(x), b(x));
            }
            throw new Error('unknown function: ' + name + '/' + args.length);
          }
          if (name === 'x') return (x) => x;
          if (CONSTS[name] !== undefined) { const c = CONSTS[name]; return () => c; }
          throw new Error('unknown identifier: ' + name);
        }
        throw new Error('unexpected token');
      }
      const fn = parseAdd();
      if (pos < toks.length) throw new Error('trailing tokens');
      return fn;
    }

    const SVG_NS = 'http://www.w3.org/2000/svg';
    const W = 400, H = 280, PAD = 24;
    const PLOT_W = W - PAD * 2;
    const PLOT_H = H - PAD * 2;
    const xToPx = (xv: number) => PAD + ((xv - xMin) / (xMax - xMin)) * PLOT_W;
    const yToPx = (yv: number) => PAD + (1 - (yv - yMin) / (yMax - yMin)) * PLOT_H;

    const style = document.createElement('style');
    style.textContent = `
      .fp-root { display: grid; gap: 6px; }
      .fp-title { font-family: "Fraunces", Georgia, serif; font-size: 16px; font-weight: 600; margin: 0; }
      .fp-expr { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; color: #4B463E; margin: 0; }
      .fp-err { color: #9B1C1C; font-size: 12px; margin: 0; }
    `;
    ctx.mount.appendChild(style);

    const root = document.createElement('div');
    root.className = 'fp-root';
    ctx.mount.appendChild(root);

    if (title) {
      const t = document.createElement('p');
      t.className = 'fp-title';
      t.textContent = title;
      root.appendChild(t);
    }
    const exprLabel = document.createElement('p');
    exprLabel.className = 'fp-expr';
    exprLabel.textContent = 'y = ' + expr;
    root.appendChild(exprLabel);

    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', String(H));
    svg.setAttribute('aria-label', title || 'Function plot');
    root.appendChild(svg);

    const frame = document.createElementNS(SVG_NS, 'rect');
    frame.setAttribute('x', String(PAD));
    frame.setAttribute('y', String(PAD));
    frame.setAttribute('width', String(PLOT_W));
    frame.setAttribute('height', String(PLOT_H));
    frame.setAttribute('fill', '#FFFDF7');
    frame.setAttribute('stroke', '#1B1A17');
    frame.setAttribute('stroke-width', '1.5');
    svg.appendChild(frame);

    function addLine(x1: number, y1: number, x2: number, y2: number, color: string, w: number) {
      const ln = document.createElementNS(SVG_NS, 'line');
      ln.setAttribute('x1', String(x1));
      ln.setAttribute('y1', String(y1));
      ln.setAttribute('x2', String(x2));
      ln.setAttribute('y2', String(y2));
      ln.setAttribute('stroke', color);
      ln.setAttribute('stroke-width', String(w));
      svg.appendChild(ln);
    }
    for (let gx = Math.ceil(xMin); gx <= Math.floor(xMax); gx++) {
      addLine(xToPx(gx), PAD, xToPx(gx), PAD + PLOT_H, '#E7E2D3', 0.5);
    }
    for (let gy = Math.ceil(yMin); gy <= Math.floor(yMax); gy++) {
      addLine(PAD, yToPx(gy), PAD + PLOT_W, yToPx(gy), '#E7E2D3', 0.5);
    }
    if (xMin <= 0 && xMax >= 0) addLine(xToPx(0), PAD, xToPx(0), PAD + PLOT_H, '#4B463E', 1);
    if (yMin <= 0 && yMax >= 0) addLine(PAD, yToPx(0), PAD + PLOT_W, yToPx(0), '#4B463E', 1);

    let compiled: ((x: number) => number) | null = null;
    try {
      compiled = compile(expr);
    } catch (err) {
      const e = document.createElement('p');
      e.className = 'fp-err';
      e.textContent = 'Could not plot — ' + (err instanceof Error ? err.message : String(err));
      root.appendChild(e);
    }

    if (compiled) {
      const SAMPLES = 200;
      const pts: string[] = [];
      let prevValid = false;
      for (let i = 0; i <= SAMPLES; i++) {
        const xv = xMin + (i / SAMPLES) * (xMax - xMin);
        let yv: number;
        try { yv = compiled(xv); } catch { yv = NaN; }
        if (!Number.isFinite(yv)) { prevValid = false; continue; }
        const cy = Math.max(PAD - 200, Math.min(PAD + PLOT_H + 200, yToPx(yv)));
        pts.push((prevValid ? 'L' : 'M') + xToPx(xv).toFixed(2) + ' ' + cy.toFixed(2));
        prevValid = true;
      }
      if (pts.length > 0) {
        const path = document.createElementNS(SVG_NS, 'path');
        path.setAttribute('d', pts.join(' '));
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#FF6F00');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-linecap', 'round');
        svg.appendChild(path);
      }
    }
  },
});
