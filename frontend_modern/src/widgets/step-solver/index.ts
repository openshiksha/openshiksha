/**
 * `step-solver` — the Phase-2 **Guided Step-Validator** widget (GSV-2b of the
 * AI-Native Interactive Learning initiative).
 *
 * The student solves the `prompt` equation/expression **one line at a time**.
 * As they type each line, a **deterministic algebraic-equivalence engine** —
 * run *inside the sandbox*, never AI — checks the new line against the line
 * directly above it and shows live ✓ / ✗. The student's final line is reported
 * through `ctx.reportValue` into the existing per-subpart grader, exactly like
 * `number-line`. **AI is nowhere near this widget**: correctness here is the
 * same deterministic numeric-probing algorithm as the backend GSV-1 engine.
 *
 * Why the engine is inlined here
 * ------------------------------
 * The widget runtime is a `sandbox="allow-scripts"` iframe **without**
 * `allow-same-origin`: it is deterministic and **network-less** by design, and
 * `render` is serialised via `Function.prototype.toString()` and inlined into
 * the boot script — it cannot import app modules or capture closures. So the
 * live per-line check cannot round-trip to the backend GSV-1 endpoint, and it
 * cannot `import` the sibling `algebra.ts` either. It must be **self-contained**
 * sandbox JS. This file therefore inlines a faithful port of `./algebra.ts`
 * (itself the TS port of `apps/core/algebra.py`) — the same grammar, whitelist,
 * seeded probing, and equation/expression semantics. The two are kept honest by
 * `index.test.ts`, which drives this widget over a battery of line pairs and
 * asserts the on-screen ✓/✗ matches `checkStep` from `algebra.ts` exactly.
 * This is the same in-sandbox-deterministic-evaluator pattern the
 * `function-plotter` widget established.
 *
 * The engine **never throws into the UI**: a malformed line yields a neutral
 * "can't check this yet" state, never a crash — the deterministic fallback.
 */

import { defineWidget } from '../_sdk/defineWidget';
import type { WidgetContext } from '../_sdk/defineWidget';
import paramsSchema from './params.schema.json';

interface StepSolverConfig {
  /** Starting equation/expression shown as the fixed first line. */
  prompt?: string;
  /** Optional instruction above the steps. */
  label?: string;
  /** Max number of student step lines (excluding the prompt). Default 8. */
  maxLines?: number;
}

/**
 * Sandbox-side render. Exported so the Vitest suite can execute it against a
 * happy-dom DOM and assert the live-check behaviour + anti-drift parity with
 * `algebra.ts`. Must stay **self-contained** (no captured closures / imports) —
 * the runtime stringifies it into the iframe boot.
 */
export const render = (ctx: WidgetContext): void => {
  const cfg = ctx.config as StepSolverConfig;
  const prompt = typeof cfg.prompt === 'string' && cfg.prompt.trim() ? cfg.prompt.trim() : 'x + 1 = 2';
  const label = typeof cfg.label === 'string' ? cfg.label : '';
  const maxLines =
    Number.isInteger(cfg.maxLines) && (cfg.maxLines as number) >= 2 ? (cfg.maxLines as number) : 8;

  // ───────────────────────────────────────────────────────────────────────
  // Deterministic equivalence engine — in-sandbox port of ./algebra.ts.
  // Never AI. Never throws into the caller. Verdict-for-verdict identical to
  // `algebra.ts` (same seed / tolerance / sampling), enforced by the test.
  // ───────────────────────────────────────────────────────────────────────
  type Env = Record<string, number>;
  type Compiled = (env: Env) => number;
  type Comp = { fn: Compiled; freeVars: string[] };
  interface StepResult {
    equivalent: boolean;
    reason: string;
    error: string | null;
  }

  const UNARY_FUNCS: Record<string, (n: number) => number> = {
    sin: Math.sin,
    cos: Math.cos,
    tan: Math.tan,
    asin: Math.asin,
    acos: Math.acos,
    atan: Math.atan,
    sinh: Math.sinh,
    cosh: Math.cosh,
    tanh: Math.tanh,
    ln: Math.log,
    log: Math.log10,
    exp: Math.exp,
    sqrt: Math.sqrt,
    abs: Math.abs,
  };
  const CONSTANTS: Record<string, number> = { pi: Math.PI, e: Math.E };

  const isDigit = (c: string): boolean => c >= '0' && c <= '9';
  const isAlpha = (c: string): boolean =>
    (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c === '_';
  const isAlnum = (c: string): boolean => isAlpha(c) || isDigit(c);

  type Token = { k: string; v?: number | string };

  function tokenise(src: string): Token[] {
    const toks: Token[] = [];
    let i = 0;
    const n = src.length;
    while (i < n) {
      const c = src[i];
      if (/\s/.test(c)) {
        i += 1;
        continue;
      }
      if ('+-*/^(),'.indexOf(c) !== -1) {
        toks.push({ k: c });
        i += 1;
        continue;
      }
      if (isDigit(c) || c === '.') {
        let j = i;
        let seenDot = false;
        while (j < n && (isDigit(src[j]) || src[j] === '.')) {
          if (src[j] === '.') {
            if (seenDot) throw new Error('malformed number');
            seenDot = true;
          }
          j += 1;
        }
        const num = Number(src.slice(i, j));
        if (!Number.isFinite(num)) throw new Error('bad number');
        toks.push({ k: 'num', v: num });
        i = j;
        continue;
      }
      if (isAlpha(c)) {
        let j = i;
        while (j < n && isAlnum(src[j])) j += 1;
        toks.push({ k: 'name', v: src.slice(i, j) });
        i = j;
        continue;
      }
      throw new Error('unexpected character ' + c);
    }
    return toks;
  }

  function compile(src: string): Comp {
    const toks = tokenise(src);
    const freeVars = new Set<string>();
    let pos = 0;
    const peek = (): Token | undefined => toks[pos];

    function parseAdd(): Compiled {
      let left = parseMul();
      for (;;) {
        const t = peek();
        if (t && (t.k === '+' || t.k === '-')) {
          const op = t.k;
          pos += 1;
          const right = parseMul();
          const l = left;
          left = op === '+' ? (e: Env): number => l(e) + right(e) : (e: Env): number => l(e) - right(e);
        } else {
          return left;
        }
      }
    }
    function parseMul(): Compiled {
      let left = parsePow();
      for (;;) {
        const t = peek();
        if (t && (t.k === '*' || t.k === '/')) {
          const op = t.k;
          pos += 1;
          const right = parsePow();
          const l = left;
          left = op === '*' ? (e: Env): number => l(e) * right(e) : (e: Env): number => l(e) / right(e);
        } else if (t && (t.k === 'num' || t.k === 'name' || t.k === '(')) {
          // Implicit multiplication: juxtaposition with no operator (2x, 3(x+1)).
          const right = parsePow();
          const l = left;
          left = (e: Env): number => l(e) * right(e);
        } else {
          return left;
        }
      }
    }
    function parsePow(): Compiled {
      const base = parseUnary();
      const t = peek();
      if (t && t.k === '^') {
        pos += 1;
        const ex = parsePow(); // right-associative
        return (e: Env): number => Math.pow(base(e), ex(e));
      }
      return base;
    }
    function parseUnary(): Compiled {
      const t = peek();
      if (t && t.k === '-') {
        pos += 1;
        const inner = parseUnary();
        return (e: Env): number => -inner(e);
      }
      if (t && t.k === '+') {
        pos += 1;
        return parseUnary();
      }
      return parseAtom();
    }
    function parseAtom(): Compiled {
      const t = peek();
      if (t === undefined) throw new Error('unexpected end of expression');
      if (t.k === 'num') {
        pos += 1;
        const v = t.v as number;
        return (): number => v;
      }
      if (t.k === '(') {
        pos += 1;
        const inner = parseAdd();
        const close = peek();
        if (!close || close.k !== ')') throw new Error('missing closing parenthesis');
        pos += 1;
        return inner;
      }
      if (t.k === 'name') {
        pos += 1;
        const name = t.v as string;
        const nxt = peek();
        if (nxt && nxt.k === '(' && name in UNARY_FUNCS) {
          pos += 1; // consume '('
          const arg = parseAdd();
          const close = peek();
          if (!close || close.k !== ')') throw new Error('missing ) after ' + name + '(');
          pos += 1;
          const fn = UNARY_FUNCS[name];
          return (e: Env): number => fn(arg(e));
        }
        if (name in CONSTANTS) {
          const c = CONSTANTS[name];
          return (): number => c;
        }
        if (name in UNARY_FUNCS) throw new Error('function ' + name + ' used without arguments');
        freeVars.add(name);
        return (e: Env): number => e[name];
      }
      throw new Error('unexpected token ' + t.k);
    }

    if (toks.length === 0) throw new Error('empty expression');
    const node = parseAdd();
    if (pos !== toks.length) throw new Error('trailing tokens after a complete expression');
    return { fn: node, freeVars: Array.from(freeVars) };
  }

  // Probing constants — identical to algebra.ts so verdicts match.
  const PROBE_SEED = 1618033;
  const REQUIRED_SAMPLES = 24;
  const MAX_DRAWS = 400;
  const REL_TOL = 1e-6;
  const ABS_TOL = 1e-9;
  const SAMPLE_LO = -7;
  const SAMPLE_HI = 7;

  function mulberry32(seed: number): () => number {
    let a = seed >>> 0;
    return function next(): number {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function isClose(a: number, b: number, relTol = REL_TOL, absTol = ABS_TOL): boolean {
    return Math.abs(a - b) <= Math.max(relTol * Math.max(Math.abs(a), Math.abs(b)), absTol);
  }
  function valuesClose(a: number, b: number): boolean {
    if (!Number.isFinite(a) || !Number.isFinite(b)) return false;
    return isClose(a, b);
  }
  function samplePoints(freeVars: string[], rng: () => number): Env[] {
    const points: Env[] = [];
    for (let d = 0; d < MAX_DRAWS; d += 1) {
      const env: Env = {};
      for (const v of freeVars) env[v] = SAMPLE_LO + rng() * (SAMPLE_HI - SAMPLE_LO);
      points.push(env);
    }
    return points;
  }
  function res(equivalent: boolean, reason: string, error: string | null = null): StepResult {
    return { equivalent, reason, error };
  }

  function areExpressionsEquivalent(a: string, b: string): StepResult {
    let ca: Comp;
    let cb: Comp;
    try {
      ca = compile(a);
      cb = compile(b);
    } catch (exc) {
      return res(false, 'Could not read this line.', String(exc));
    }
    const free = Array.from(new Set([...ca.freeVars, ...cb.freeVars])).sort();
    const rng = mulberry32(PROBE_SEED);
    let valid = 0;
    if (free.length === 0) {
      const va = ca.fn({});
      const vb = cb.fn({});
      if (!Number.isFinite(va) || !Number.isFinite(vb)) {
        return res(false, 'This line is undefined.', 'non-finite constant');
      }
      return valuesClose(va, vb)
        ? res(true, 'Both sides are equal.')
        : res(false, 'The two sides are not equal.');
    }
    for (const env of samplePoints(free, rng)) {
      const va = ca.fn(env);
      const vb = cb.fn(env);
      if (!Number.isFinite(va) || !Number.isFinite(vb)) continue; // singular sample
      if (!valuesClose(va, vb)) return res(false, 'This is not equal to the line above.');
      valid += 1;
      if (valid >= REQUIRED_SAMPLES) return res(true, 'Equal to the line above.');
    }
    if (valid === 0) return res(false, 'Could not check this line.', 'all samples singular');
    return res(true, 'Equal to the line above.');
  }

  function splitEquation(line: string): [string, string] | null {
    const parts = line.split('=');
    if (parts.length !== 2) return null;
    const lhs = parts[0].trim();
    const rhs = parts[1].trim();
    if (!lhs || !rhs) return null;
    return [lhs, rhs];
  }

  function areEquationsEquivalent(a: string, b: string): StepResult {
    const sa = splitEquation(a);
    const sb = splitEquation(b);
    if (sa === null || sb === null) {
      return res(false, 'This is not a single equation.', "expected one '='");
    }
    let ca: Comp;
    let cb: Comp;
    try {
      ca = compile('(' + sa[0] + ') - (' + sa[1] + ')');
      cb = compile('(' + sb[0] + ') - (' + sb[1] + ')');
    } catch (exc) {
      return res(false, 'Could not read this line.', String(exc));
    }
    const free = Array.from(new Set([...ca.freeVars, ...cb.freeVars])).sort();
    const rng = mulberry32(PROBE_SEED);
    let ratio: number | null = null;
    let aAllZero = true;
    let bAllZero = true;
    let valid = 0;
    const points = free.length ? samplePoints(free, rng) : [{}];
    for (const env of points) {
      const va = ca.fn(env);
      const vb = cb.fn(env);
      if (!Number.isFinite(va) || !Number.isFinite(vb)) continue;
      valid += 1;
      const za = isClose(va, 0, 0, ABS_TOL);
      const zb = isClose(vb, 0, 0, ABS_TOL);
      aAllZero = aAllZero && za;
      bAllZero = bAllZero && zb;
      if (!za && !zb) {
        const r = va / vb;
        if (ratio === null) ratio = r;
        else if (!isClose(ratio, r)) return res(false, 'This changes the solution.');
      } else if (za !== zb) {
        return res(false, 'This changes the solution.');
      }
      if (valid >= REQUIRED_SAMPLES) break;
    }
    if (valid === 0) return res(false, 'Could not check this line.', 'all samples singular');
    if (aAllZero && bAllZero) return res(true, 'Always true (an identity).');
    if (aAllZero !== bAllZero) return res(false, 'This changes the solution.');
    if (ratio === null || isClose(ratio, 0, 0, ABS_TOL)) return res(false, 'This changes the solution.');
    return res(true, 'Same solution as the line above.');
  }

  function countEquals(s: string): number {
    let n = 0;
    for (const c of s) if (c === '=') n += 1;
    return n;
  }

  function checkStep(previous: string, current: string): StepResult {
    const prev = previous.trim();
    const cur = current.trim();
    if (!prev || !cur) return res(false, 'Empty line.', 'empty line');
    if (countEquals(previous) > 1 || countEquals(current) > 1) {
      return res(false, "A line has more than one '='.", "multiple '='");
    }
    const prevIsEq = splitEquation(prev) !== null;
    const curIsEq = splitEquation(cur) !== null;
    if (prevIsEq && curIsEq) return areEquationsEquivalent(prev, cur);
    if (!prevIsEq && !curIsEq) return areExpressionsEquivalent(prev, cur);
    return res(false, "Mix of an equation and an expression.", 'mixed equation/expression');
  }

  // ───────────────────────────────────────────────────────────────────────
  // UI
  // ───────────────────────────────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    .ss-root { display: grid; gap: 10px; }
    .ss-label { font-size: 14px; font-weight: 600; margin: 0; }
    .ss-steps { display: grid; gap: 8px; }
    .ss-row { display: grid; grid-template-columns: 24px 1fr; align-items: center; gap: 8px; }
    .ss-prompt { font-family: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;
      font-size: 15px; background: #FFFFFF; border: 1px solid #BDB6A5; border-radius: 8px;
      padding: 8px 10px; color: #1B1A17; }
    .ss-input { font-family: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;
      font-size: 15px; border: 1px solid #BDB6A5; border-radius: 8px; padding: 8px 10px;
      color: #1B1A17; background: #FBF7EE; width: 100%; box-sizing: border-box; }
    .ss-input:focus { outline: 2px solid #FF6F00; outline-offset: 1px; border-color: #FF6F00; }
    .ss-mark { font-size: 16px; text-align: center; font-weight: 700; line-height: 1; }
    .ss-mark[data-state="ok"] { color: #15803D; }
    .ss-mark[data-state="bad"] { color: #B91C1C; }
    .ss-mark[data-state="neutral"] { color: transparent; }
    .ss-reason { font-size: 12px; margin: 0 0 0 32px; min-height: 14px; }
    .ss-reason[data-state="ok"] { color: #15803D; }
    .ss-reason[data-state="bad"] { color: #B91C1C; }
    .ss-reason[data-state="neutral"] { color: #6B6357; }
    .ss-add { justify-self: start; font-size: 13px; font-weight: 600; cursor: pointer;
      background: #FFFFFF; border: 1px solid #BDB6A5; border-radius: 8px; padding: 6px 12px;
      color: #1B1A17; }
    .ss-add:disabled { opacity: 0.5; cursor: default; }
    .ss-hint { font-size: 12px; color: #6B6357; margin: 0; }
  `;
  ctx.mount.appendChild(style);

  const root = document.createElement('div');
  root.className = 'ss-root';
  ctx.mount.appendChild(root);

  if (label) {
    const labelEl = document.createElement('p');
    labelEl.className = 'ss-label';
    labelEl.textContent = label;
    root.appendChild(labelEl);
  }

  const steps = document.createElement('div');
  steps.className = 'ss-steps';
  root.appendChild(steps);

  // The prompt is line index 0 (fixed, not editable, not the answer).
  const promptRow = document.createElement('div');
  promptRow.className = 'ss-row';
  const promptMark = document.createElement('span');
  promptMark.className = 'ss-mark';
  promptMark.setAttribute('data-state', 'neutral');
  promptMark.setAttribute('aria-hidden', 'true');
  const promptBox = document.createElement('div');
  promptBox.className = 'ss-prompt';
  promptBox.textContent = prompt;
  promptRow.appendChild(promptMark);
  promptRow.appendChild(promptBox);
  steps.appendChild(promptRow);

  interface Row {
    input: HTMLInputElement;
    mark: HTMLSpanElement;
    reason: HTMLParagraphElement;
  }

  // lines[0] is the prompt; lines[i>=1] are the student's steps.
  const lines: string[] = [prompt];
  const rows: Row[] = [];
  let hasInteracted = false;

  function setState(i: number): void {
    // i is the 1-based student-row index (i.e. lines index, i >= 1).
    const row = rows[i - 1];
    const text = lines[i];
    if (!text.trim()) {
      row.mark.textContent = '';
      row.mark.setAttribute('data-state', 'neutral');
      row.reason.textContent = '';
      row.reason.setAttribute('data-state', 'neutral');
      return;
    }
    const verdict = checkStep(lines[i - 1], text);
    if (verdict.error) {
      // Deterministic fallback: an unparseable line is neutral, not a hard ✗.
      row.mark.textContent = '…';
      row.mark.setAttribute('data-state', 'neutral');
      row.reason.textContent = "Keep going — can't check this line yet.";
      row.reason.setAttribute('data-state', 'neutral');
      return;
    }
    row.mark.textContent = verdict.equivalent ? '✓' : '✗';
    row.mark.setAttribute('data-state', verdict.equivalent ? 'ok' : 'bad');
    row.reason.textContent = verdict.reason;
    row.reason.setAttribute('data-state', verdict.equivalent ? 'ok' : 'bad');
  }

  function reportLatest(): void {
    let answer = '';
    for (let i = lines.length - 1; i >= 1; i -= 1) {
      if (lines[i].trim()) {
        answer = lines[i].trim();
        break;
      }
    }
    hasInteracted = true;
    ctx.reportValue(answer);
  }

  function addRow(): void {
    if (lines.length - 1 >= maxLines) return;
    const idx = lines.length; // this row's lines index
    lines.push('');

    const row = document.createElement('div');
    row.className = 'ss-row';
    const mark = document.createElement('span');
    mark.className = 'ss-mark';
    mark.setAttribute('data-state', 'neutral');
    mark.setAttribute('role', 'img');
    mark.setAttribute('aria-live', 'polite');
    const input = document.createElement('input');
    input.className = 'ss-input';
    input.type = 'text';
    input.setAttribute('inputmode', 'text');
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('autocapitalize', 'off');
    input.setAttribute('spellcheck', 'false');
    input.setAttribute('aria-label', 'Step ' + idx);
    input.placeholder = idx === 1 ? 'Rewrite the line above…' : 'Next step…';
    row.appendChild(mark);
    row.appendChild(input);
    steps.appendChild(row);

    const reason = document.createElement('p');
    reason.className = 'ss-reason';
    reason.setAttribute('data-state', 'neutral');
    steps.appendChild(reason);

    const rowObj: Row = { input, mark, reason };
    rows.push(rowObj);

    input.addEventListener('input', () => {
      lines[idx] = input.value;
      setState(idx);
      // The line below this one compares against it, so refresh it too.
      if (idx + 1 < lines.length) setState(idx + 1);
      reportLatest();
      updateAddButton();
    });
    input.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') {
        ev.preventDefault();
        if (input.value.trim() && idx === lines.length - 1) {
          addRow();
          const next = rows[rows.length - 1];
          if (next && next.input !== input) next.input.focus();
        }
      }
    });

    input.focus();
  }

  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.className = 'ss-add';
  addBtn.textContent = '+ Add step';
  root.appendChild(addBtn);

  function updateAddButton(): void {
    const lastIsEmpty = lines.length >= 2 && !lines[lines.length - 1].trim();
    addBtn.disabled = lines.length - 1 >= maxLines || lastIsEmpty;
  }
  addBtn.addEventListener('click', () => {
    addRow();
    updateAddButton();
  });

  const hint = document.createElement('p');
  hint.className = 'ss-hint';
  hint.textContent = 'Rewrite the line above, one step per line. ✓ means it still matches.';
  root.appendChild(hint);

  // Start with one empty step ready to type. No reportValue at mount — the
  // answer stays empty until the student actually writes a step (like number-line).
  addRow();
  updateAddButton();
  void hasInteracted;
};

export default defineWidget({
  kind: 'step-solver',
  version: 1,
  meta: {
    title: 'Step solver',
    description:
      'Solve an equation one line at a time; each line is checked for algebraic equivalence (deterministic, in-sandbox) with live ✓/✗. The final line is the answer.',
    answerProducing: true,
  },
  paramsSchema,
  render,
});
