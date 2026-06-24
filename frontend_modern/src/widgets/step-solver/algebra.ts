/**
 * Deterministic algebraic-equivalence engine — the **in-sandbox** counterpart of
 * the backend `apps/core/algebra.py` (GSV-1). Increment **GSV-2a** of the
 * AI-Native Interactive Learning initiative (Phase 2: the Guided Step-Validator).
 *
 * Why a second implementation, in TypeScript?
 * -------------------------------------------
 * The widget runtime is a `sandbox="allow-scripts"` iframe **without**
 * `allow-same-origin`: it is deterministic and **network-less** by design (the
 * iron-clad bar, principle 1). The `step-solver` widget (GSV-2b) must give the
 * student instant ✓/✗ liveness as they type each line — a per-keystroke round
 * trip to the backend GSV-1 endpoint would mean a network call from inside a
 * sandbox that is forbidden to make one. So correctness for the *live* check
 * runs **here**, in the sandbox, as deterministic JS.
 *
 * This is **not** AI and never will be — equivalence is decided by the same
 * deterministic numeric-probing algorithm as the Python engine, so the
 * sandbox-ban on AI (principle 1) does not apply to it; AI (GSV-3) only ever
 * *explains* a line this engine has already judged wrong (principle 2). The two
 * engines are a faithful pair: this file mirrors `algebra.py`'s grammar,
 * whitelist, and equation/expression semantics one-to-one. The shared seam is
 * the curriculum's safe-evaluator shape, already proven in the sandbox
 * `function-plotter` widget.
 *
 * Design constraints (mirroring the iron-clad bar):
 *
 * - **No `eval` / no `Function`.** A small recursive-descent parser compiles a
 *   line into a pure closure built only from arithmetic and a fixed whitelist of
 *   functions. Nothing the student types is ever interpreted as code — exactly
 *   the pattern `function-plotter` established so contributors never copy a
 *   dangerous one forward.
 * - **No CAS / no dependency.** Equivalence is decided by **deterministic numeric
 *   probing**: both lines are evaluated at many *seeded* sample points over their
 *   free variables; they are equivalent iff they agree (within tolerance) at
 *   every valid sample. Seeded → a given pair of lines always yields the same
 *   verdict (reproducible).
 * - **Never throws into the caller.** Malformed input (a parse error, an unknown
 *   symbol, an all-singular sample set, a mixed equation/expression pair) yields
 *   a structured {@link EquivalenceResult} with `equivalent: false` and a
 *   populated `error` — the deterministic fallback. Callers get a verdict, not an
 *   exception.
 *
 * Public API:
 *
 * - {@link checkStep} — the entry point the `step-solver` widget calls per line.
 *   Auto-detects whether the two lines are *equations* (contain `=`) or bare
 *   *expressions* and dispatches accordingly.
 * - {@link areExpressionsEquivalent} / {@link areEquationsEquivalent} — the two
 *   primitives, exposed for direct use and testing.
 */

// --------------------------------------------------------------------------- //
// Result type
// --------------------------------------------------------------------------- //

/**
 * Outcome of an equivalence check.
 *
 * `equivalent` is the verdict. `reason` is a short, deterministic,
 * human-readable note (never AI-authored) describing *why* — suitable for a
 * neutral on-screen line. `error` is set only when a line could not be parsed /
 * evaluated (the fallback path); in that case `equivalent` is always `false`.
 */
export interface EquivalenceResult {
  readonly equivalent: boolean;
  readonly reason: string;
  /** Set only on the fallback path; `null` when the verdict is trustworthy. */
  readonly error: string | null;
}

/** True when the check ran without a parse/eval error (verdict is trustworthy). */
export function isTrustworthy(result: EquivalenceResult): boolean {
  return result.error === null;
}

function result(equivalent: boolean, reason: string, error: string | null = null): EquivalenceResult {
  return { equivalent, reason, error };
}

// --------------------------------------------------------------------------- //
// Safe expression parser  (numbers, variables, + - * / ^, unary -, functions)
// --------------------------------------------------------------------------- //

// Whitelisted unary functions — exactly the curriculum's set, matching the
// backend `algebra.py` and the sandbox `function-plotter`. `ln` is natural log;
// `log` is base-10.
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

// Named constants resolve to a value, never a free variable.
const CONSTANTS: Record<string, number> = {
  pi: Math.PI,
  e: Math.E,
};

/** Raised internally when a line cannot be parsed; never escapes the module. */
class ParseError extends Error {}

// --- tokeniser ------------------------------------------------------------- //

type Token =
  | { kind: 'num'; value: number }
  | { kind: 'name'; value: string }
  | { kind: '+' | '-' | '*' | '/' | '^' | '(' | ')' | ',' };

function isDigit(c: string): boolean {
  return c >= '0' && c <= '9';
}

function isAlpha(c: string): boolean {
  return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c === '_';
}

function isAlnum(c: string): boolean {
  return isAlpha(c) || isDigit(c);
}

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
    if (c === '+' || c === '-' || c === '*' || c === '/' || c === '^' || c === '(' || c === ')' || c === ',') {
      toks.push({ kind: c });
      i += 1;
      continue;
    }
    if (isDigit(c) || c === '.') {
      let j = i;
      let seenDot = false;
      while (j < n && (isDigit(src[j]) || src[j] === '.')) {
        if (src[j] === '.') {
          if (seenDot) throw new ParseError(`malformed number near ${src.slice(i, j + 1)}`);
          seenDot = true;
        }
        j += 1;
      }
      const num = Number(src.slice(i, j));
      if (!Number.isFinite(num)) throw new ParseError(`bad number ${src.slice(i, j)}`);
      toks.push({ kind: 'num', value: num });
      i = j;
      continue;
    }
    if (isAlpha(c)) {
      let j = i;
      while (j < n && isAlnum(src[j])) j += 1;
      toks.push({ kind: 'name', value: src.slice(i, j) });
      i = j;
      continue;
    }
    throw new ParseError(`unexpected character ${c}`);
  }
  return toks;
}

// --- AST node: a closure over a variable environment ----------------------- //

// A compiled expression is a callable env(Record<string, number>) -> number.
type Env = Record<string, number>;
type Compiled = (env: Env) => number;

/**
 * Recursive-descent parser with implicit multiplication.
 *
 * Grammar (lowest to highest precedence):
 *
 *     add   := mul (('+' | '-') mul)*
 *     mul   := pow (('*' | '/' | <implicit>) pow)*
 *     pow   := unary ('^' pow)?            // right-associative
 *     unary := ('+' | '-') unary | atom
 *     atom  := num | name | name '(' add ')' | '(' add ')'
 *
 * Implicit multiplication: in `mul`, if the next token can *begin* an atom (a
 * number, a name, or `(`) with no operator between, a `*` is inferred — so `2x`,
 * `3(x+1)` and `xy` parse as products. A `name` immediately followed by `(` is a
 * function call iff the name is a known function; otherwise it is a variable
 * times a parenthesised group.
 */
class Parser {
  private pos = 0;
  readonly freeVars = new Set<string>();

  constructor(private readonly toks: Token[]) {}

  private peek(): Token | undefined {
    return this.toks[this.pos];
  }

  private next(): Token {
    const tok = this.toks[this.pos];
    this.pos += 1;
    return tok;
  }

  parse(): Compiled {
    if (this.toks.length === 0) throw new ParseError('empty expression');
    const node = this.add();
    if (this.pos !== this.toks.length) {
      throw new ParseError('trailing tokens after a complete expression');
    }
    return node;
  }

  private add(): Compiled {
    let left = this.mul();
    for (;;) {
      const tok = this.peek();
      if (tok && (tok.kind === '+' || tok.kind === '-')) {
        const op = tok.kind;
        this.next();
        const right = this.mul();
        left = Parser.binop(op, left, right);
      } else {
        return left;
      }
    }
  }

  private mul(): Compiled {
    let left = this.pow();
    for (;;) {
      const tok = this.peek();
      if (tok && (tok.kind === '*' || tok.kind === '/')) {
        const op = tok.kind;
        this.next();
        const right = this.pow();
        left = Parser.binop(op, left, right);
      } else if (tok && (tok.kind === 'num' || tok.kind === 'name' || tok.kind === '(')) {
        // Implicit multiplication: juxtaposition with no operator.
        const right = this.pow();
        left = Parser.binop('*', left, right);
      } else {
        return left;
      }
    }
  }

  private pow(): Compiled {
    const base = this.unary();
    const tok = this.peek();
    if (tok && tok.kind === '^') {
      this.next();
      const exponent = this.pow(); // right-associative
      return (env) => Math.pow(base(env), exponent(env));
    }
    return base;
  }

  private unary(): Compiled {
    const tok = this.peek();
    if (tok && tok.kind === '-') {
      this.next();
      const inner = this.unary();
      return (env) => -inner(env);
    }
    if (tok && tok.kind === '+') {
      this.next();
      return this.unary();
    }
    return this.atom();
  }

  private atom(): Compiled {
    const tok = this.peek();
    if (tok === undefined) throw new ParseError('unexpected end of expression');
    if (tok.kind === 'num') {
      this.next();
      const v = tok.value;
      return () => v;
    }
    if (tok.kind === '(') {
      this.next();
      const inner = this.add();
      const close = this.peek();
      if (!close || close.kind !== ')') throw new ParseError('missing closing parenthesis');
      this.next();
      return inner;
    }
    if (tok.kind === 'name') {
      this.next();
      const name = tok.value;
      const nxt = this.peek();
      if (nxt && nxt.kind === '(' && name in UNARY_FUNCS) {
        this.next(); // consume '('
        const arg = this.add();
        const close = this.peek();
        if (!close || close.kind !== ')') throw new ParseError(`missing ')' after ${name}(`);
        this.next();
        const fn = UNARY_FUNCS[name];
        return (env) => fn(arg(env));
      }
      if (name in CONSTANTS) {
        const c = CONSTANTS[name];
        return () => c;
      }
      if (name in UNARY_FUNCS) {
        throw new ParseError(`function ${name} used without arguments`);
      }
      // A bare identifier is a free variable.
      this.freeVars.add(name);
      return (env) => env[name];
    }
    throw new ParseError(`unexpected token ${tok.kind}`);
  }

  private static binop(op: '+' | '-' | '*' | '/', left: Compiled, right: Compiled): Compiled {
    switch (op) {
      case '+':
        return (env) => left(env) + right(env);
      case '-':
        return (env) => left(env) - right(env);
      case '*':
        return (env) => left(env) * right(env);
      case '/':
        return (env) => left(env) / right(env);
    }
  }
}

interface Compiled1 {
  fn: Compiled;
  freeVars: string[];
}

/** Parse `src` into `{ fn, freeVars }`. Throws {@link ParseError} on bad input. */
function compile(src: string): Compiled1 {
  const parser = new Parser(tokenise(src));
  const fn = parser.parse();
  return { fn, freeVars: [...parser.freeVars] };
}

// --------------------------------------------------------------------------- //
// Numeric-probing equivalence
// --------------------------------------------------------------------------- //

// Deterministic seed so a given pair of lines always yields the same verdict.
const PROBE_SEED = 1_618_033;
// How many sample points we *want* to agree on before declaring equivalence.
const REQUIRED_SAMPLES = 24;
// How many draws we are willing to attempt to reach that many valid samples
// (some draws hit singularities — sqrt of a negative, division by zero, …).
const MAX_DRAWS = 400;
// Relative + absolute tolerance for "the two values are equal".
const REL_TOL = 1e-6;
const ABS_TOL = 1e-9;
// Range from which sample values for each free variable are drawn.
const SAMPLE_LO = -7.0;
const SAMPLE_HI = 7.0;

/**
 * `mulberry32` — a tiny, fast, fully deterministic 32-bit PRNG. JS has no
 * seedable RNG in the standard library, and the sandbox must stay network-less
 * and dependency-free, so we roll a 9-line one. The exact draws differ from the
 * Python engine's `random.Random`, but that is irrelevant: equivalence is a
 * property of the *expressions*, not of the sample points, and a uniform draw
 * over `[SAMPLE_LO, SAMPLE_HI]` is all the algorithm needs. Seeded → reproducible.
 */
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

/** Python `math.isclose(a, b, rel_tol, abs_tol)`. */
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

function formatWhere(env: Env, free: string[]): string {
  return free.map((k) => `${k}=${env[k].toPrecision(3)}`).join(', ');
}

/**
 * Decide whether two **expressions** are algebraically equivalent.
 *
 * Equivalent ⟺ they evaluate equally at every valid sample point over the
 * *union* of their free variables. Constant expressions (no free variables) are
 * compared at a single point.
 */
export function areExpressionsEquivalent(a: string, b: string): EquivalenceResult {
  let ca: Compiled1;
  let cb: Compiled1;
  try {
    ca = compile(a);
    cb = compile(b);
  } catch (exc) {
    return result(false, 'Could not parse a line.', errorMessage(exc));
  }

  const free = [...new Set([...ca.freeVars, ...cb.freeVars])].sort();
  const rng = mulberry32(PROBE_SEED);

  let valid = 0;
  if (free.length === 0) {
    // Both constant: a single evaluation settles it.
    const va = ca.fn({});
    const vb = cb.fn({});
    if (!Number.isFinite(va) || !Number.isFinite(vb)) {
      return result(false, 'A line is undefined.', 'a constant line evaluates to a non-finite value');
    }
    if (valuesClose(va, vb)) return result(true, 'Both sides are equal constants.');
    return result(false, `The two sides differ (${formatNum(va)} vs ${formatNum(vb)}).`);
  }

  for (const env of samplePoints(free, rng)) {
    const va = ca.fn(env);
    const vb = cb.fn(env);
    if (!Number.isFinite(va) || !Number.isFinite(vb)) continue; // singular sample — skip
    if (!valuesClose(va, vb)) {
      return result(false, `The two sides differ at ${formatWhere(env, free)}.`);
    }
    valid += 1;
    if (valid >= REQUIRED_SAMPLES) {
      return result(true, 'Both sides match across all sampled values.');
    }
  }

  if (valid === 0) {
    return result(
      false,
      'Could not evaluate the lines (no valid sample points).',
      'all sample points were singular',
    );
  }
  // Agreed on every valid sample we managed to draw, just fewer than the target.
  return result(true, 'Both sides match across all sampled values.');
}

/** Split `L = R` into `[L, R]`; `null` if it isn't a single equation. */
function splitEquation(line: string): [string, string] | null {
  const parts = line.split('=');
  if (parts.length !== 2) return null;
  const lhs = parts[0].trim();
  const rhs = parts[1].trim();
  if (!lhs || !rhs) return null;
  return [lhs, rhs];
}

/**
 * Decide whether two **equations** `L = R` have the same solution set.
 *
 * Each equation is normalised to `L - R` (whose zero set is the solution set).
 * The two are equivalent iff one normal form is a **non-zero constant multiple**
 * of the other across all sampled points — capturing the legal moves of equation
 * solving (add/subtract the same thing, multiply/divide both sides by a non-zero
 * constant, rearrange). `0 = 0` is equivalent only to another identity.
 */
export function areEquationsEquivalent(a: string, b: string): EquivalenceResult {
  const splitA = splitEquation(a);
  const splitB = splitEquation(b);
  if (splitA === null || splitB === null) {
    return result(false, 'A line is not a single equation.', "expected exactly one '=' on each line");
  }

  // Normal form L - R, as an expression string, reusing the parser.
  const normA = `(${splitA[0]}) - (${splitA[1]})`;
  const normB = `(${splitB[0]}) - (${splitB[1]})`;
  let ca: Compiled1;
  let cb: Compiled1;
  try {
    ca = compile(normA);
    cb = compile(normB);
  } catch (exc) {
    return result(false, 'Could not parse a line.', errorMessage(exc));
  }

  const free = [...new Set([...ca.freeVars, ...cb.freeVars])].sort();
  const rng = mulberry32(PROBE_SEED);

  let ratio: number | null = null;
  let aAllZero = true;
  let bAllZero = true;
  let valid = 0;

  // Constant equations (e.g. `2 = 2`) need one point.
  const points = free.length ? samplePoints(free, rng) : [{}];
  for (const env of points) {
    const va = ca.fn(env);
    const vb = cb.fn(env);
    if (!Number.isFinite(va) || !Number.isFinite(vb)) continue;
    valid += 1;

    const za = isClose(va, 0.0, 0, ABS_TOL);
    const zb = isClose(vb, 0.0, 0, ABS_TOL);
    aAllZero = aAllZero && za;
    bAllZero = bAllZero && zb;

    if (!za && !zb) {
      const r = va / vb;
      if (ratio === null) {
        ratio = r;
      } else if (!isClose(ratio, r)) {
        const where = formatWhere(env, free) || 'the constants';
        return result(false, `These equations have different solutions (at ${where}).`);
      }
    } else if (za !== zb) {
      // One side is zero where the other isn't → solution sets diverge.
      const where = formatWhere(env, free) || 'a tested value';
      return result(false, `These equations have different solutions (at ${where}).`);
    }
    if (valid >= REQUIRED_SAMPLES) break;
  }

  if (valid === 0) {
    return result(false, 'Could not evaluate the equations.', 'all sample points were singular');
  }
  if (aAllZero && bAllZero) return result(true, 'Both are identities (always true).');
  if (aAllZero !== bAllZero) return result(false, 'These equations have different solutions.');
  if (ratio === null || isClose(ratio, 0.0, 0, ABS_TOL)) {
    // Couldn't establish a non-zero proportionality constant.
    return result(false, 'These equations have different solutions.');
  }
  return result(true, 'These equations have the same solution.');
}

/**
 * Top-level entry: is `current` a valid algebraic step from `previous`?
 *
 * Auto-detects the form. If **both** lines contain exactly one `=` they are
 * compared as *equations* (same solution set); otherwise they are compared as
 * bare *expressions* (equal everywhere). A mixed pair (one equation, one
 * expression) is rejected with an `error` — the deterministic fallback.
 *
 * This never throws: every malformed input returns an {@link EquivalenceResult}
 * with `equivalent: false` and a populated `error`.
 */
export function checkStep(previous: unknown, current: unknown): EquivalenceResult {
  if (typeof previous !== 'string' || typeof current !== 'string') {
    return result(false, 'A line was not text.', 'non-string input');
  }
  const prev = previous.trim();
  const cur = current.trim();
  if (!prev || !cur) {
    return result(false, 'A line was empty.', 'empty line');
  }

  // A bare "=" count mismatch (e.g. two '=' signs) → treat as parse error.
  if (countEquals(previous) > 1 || countEquals(current) > 1) {
    return result(false, "A line has more than one '='.", "multiple '=' on a line");
  }

  const prevIsEq = splitEquation(prev) !== null;
  const curIsEq = splitEquation(cur) !== null;

  if (prevIsEq && curIsEq) return areEquationsEquivalent(prev, cur);
  if (!prevIsEq && !curIsEq) return areExpressionsEquivalent(prev, cur);
  return result(
    false,
    "One line is an equation and the other isn't.",
    'cannot compare an equation with a bare expression',
  );
}

// --- small helpers --------------------------------------------------------- //

function countEquals(s: string): number {
  let n = 0;
  for (const c of s) if (c === '=') n += 1;
  return n;
}

function errorMessage(exc: unknown): string {
  return exc instanceof Error ? exc.message : String(exc);
}

/** Python `%g`-ish compact number formatting for the neutral reason strings. */
function formatNum(v: number): string {
  return Number.isInteger(v) ? String(v) : String(Number(v.toPrecision(6)));
}
