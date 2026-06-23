"""
Deterministic algebraic-equivalence engine for the Guided Step-Validator
(Phase 2 of the AI-Native Interactive Learning initiative, increment **GSV-1**).

This is the **correctness keystone** for the step validator: when a student
solves an equation line by line, *this* module — never an LLM — decides whether
each new line is algebraically equivalent to the previous one. AI (a later
increment) may only **explain** a line this engine has already judged wrong; it
is never in the correctness path.

Design constraints (mirroring the iron-clad bar):

* **No ``eval`` / no ``exec`` / no code execution.** A small recursive-descent
  parser compiles a curriculum-level math expression into a pure Python callable
  built only from arithmetic and a fixed whitelist of functions. Nothing the
  student types is ever interpreted as code. This mirrors the sandbox-side
  ``function-plotter`` evaluator (``frontend_modern/src/widgets/function-plotter``),
  re-implemented server-side so correctness is decided on the host.
* **No new dependency / no CAS.** There is no ``sympy`` in the stack and we keep
  it that way. Equivalence is decided by **deterministic numeric probing**:
  both expressions are evaluated at many *fixed-seed* sample points over their
  free variables; they are equivalent iff they agree (within tolerance) at every
  valid sample. For the polynomial / rational / transcendental expressions the
  curriculum uses this is reliable, and — being seeded — it is reproducible.
* **Never raises into the caller.** Malformed input (a parse error, an unknown
  symbol, an all-singular sample set) yields a structured
  :class:`EquivalenceResult` with ``equivalent=False`` and a populated
  ``error`` — the deterministic fallback. Callers get a verdict, not a 500.

Public API:

* :func:`check_step` — the entry point a future GSV endpoint calls. Auto-detects
  whether the two lines are *equations* (contain ``=``) or bare *expressions*
  and dispatches accordingly. Returns an :class:`EquivalenceResult`.
* :func:`are_expressions_equivalent` / :func:`are_equations_equivalent` — the
  two primitives, exposed for direct use and testing.

Equation equivalence: an equation ``L = R`` is normalised to the expression
``L - R`` (its zero set is the solution set). Two equations are equivalent iff
their normal forms have the **same solution set**, which for this engine means
one is a non-zero constant multiple of the other across all samples (so
``2x = 6`` ≡ ``x = 3`` ≡ ``4x - 12 = 0``). The degenerate ``0 = 0`` identity is
equivalent only to another identity.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Set, Tuple, cast

# --------------------------------------------------------------------------- #
# Result type
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EquivalenceResult:
    """Outcome of an equivalence check.

    ``equivalent`` is the verdict. ``reason`` is a short, deterministic,
    human-readable note (never AI-authored) describing *why* — suitable for a
    neutral on-screen line. ``error`` is set only when a line could not be
    parsed / evaluated (the fallback path); in that case ``equivalent`` is
    always ``False``.
    """

    equivalent: bool
    reason: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        """True when the check ran without a parse/eval error (verdict is trustworthy)."""
        return self.error is None


# --------------------------------------------------------------------------- #
# Safe expression parser  (numbers, variables, + - * / ^, unary -, functions)
# --------------------------------------------------------------------------- #

# Whitelisted unary functions — exactly the curriculum's set, matching the
# sandbox function-plotter. ``ln`` is natural log; ``log`` is base-10.
_UNARY_FUNCS: Dict[str, Callable[[float], float]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "ln": math.log,
    "log": math.log10,
    "exp": math.exp,
    "sqrt": math.sqrt,
    "abs": abs,
}

# Named constants resolve to a value, never a free variable.
_CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}


class _ParseError(ValueError):
    """Raised internally when a line cannot be parsed; never escapes the module."""


# --- tokeniser ------------------------------------------------------------- #

_Token = Tuple[str, object]  # (kind, value)


def _tokenise(src: str) -> List[_Token]:
    toks: List[_Token] = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if c in "+-*/^(),":
            toks.append((c, c))
            i += 1
            continue
        if c.isdigit() or c == ".":
            j = i
            seen_dot = False
            while j < n and (src[j].isdigit() or src[j] == "."):
                if src[j] == ".":
                    if seen_dot:
                        raise _ParseError(f"malformed number near {src[i:j+1]!r}")
                    seen_dot = True
                j += 1
            try:
                toks.append(("num", float(src[i:j])))
            except ValueError as exc:  # pragma: no cover - guarded by the scan above
                raise _ParseError(f"bad number {src[i:j]!r}") from exc
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            toks.append(("name", src[i:j]))
            i = j
            continue
        raise _ParseError(f"unexpected character {c!r}")
    return toks


# --- AST node: a closure over a variable environment ----------------------- #

# A compiled expression is a callable env(dict[str, float]) -> float.
_Compiled = Callable[[Dict[str, float]], float]


class _Parser:
    """Recursive-descent parser with implicit multiplication.

    Grammar (lowest to highest precedence)::

        add   := mul (('+' | '-') mul)*
        mul   := pow (('*' | '/' | <implicit>) pow)*
        pow   := unary ('^' pow)?            # right-associative
        unary := ('+' | '-') unary | atom
        atom  := num | name | name '(' add ')' | '(' add ')'

    Implicit multiplication: in ``mul``, if the next token can *begin* an atom
    (a number, a name, or ``(``) with no operator between, a ``*`` is inferred —
    so ``2x``, ``3(x+1)`` and ``xy`` parse as products. A ``name`` immediately
    followed by ``(`` is a function call iff the name is a known function;
    otherwise it is a variable times a parenthesised group.
    """

    def __init__(self, toks: List[_Token]):
        self._toks = toks
        self._pos = 0
        self.free_vars: Set[str] = set()

    # -- helpers -- #
    def _peek(self) -> _Token | None:
        return self._toks[self._pos] if self._pos < len(self._toks) else None

    def _next(self) -> _Token:
        tok = self._toks[self._pos]
        self._pos += 1
        return tok

    def parse(self) -> _Compiled:
        if not self._toks:
            raise _ParseError("empty expression")
        node = self._add()
        if self._pos != len(self._toks):
            raise _ParseError("trailing tokens after a complete expression")
        return node

    # -- grammar -- #
    def _add(self) -> _Compiled:
        left = self._mul()
        while True:
            tok = self._peek()
            if tok and tok[0] in ("+", "-"):
                op = self._next()[0]
                right = self._mul()
                left = self._binop(op, left, right)
            else:
                return left

    def _mul(self) -> _Compiled:
        left = self._pow()
        while True:
            tok = self._peek()
            if tok and tok[0] in ("*", "/"):
                op = self._next()[0]
                right = self._pow()
                left = self._binop(op, left, right)
            elif tok and tok[0] in ("num", "name", "("):
                # Implicit multiplication: juxtaposition with no operator.
                right = self._pow()
                left = self._binop("*", left, right)
            else:
                return left

    def _pow(self) -> _Compiled:
        base = self._unary()
        tok = self._peek()
        if tok and tok[0] == "^":
            self._next()
            exponent = self._pow()  # right-associative
            return lambda env: math.pow(base(env), exponent(env))
        return base

    def _unary(self) -> _Compiled:
        tok = self._peek()
        if tok and tok[0] == "-":
            self._next()
            inner = self._unary()
            return lambda env: -inner(env)
        if tok and tok[0] == "+":
            self._next()
            return self._unary()
        return self._atom()

    def _atom(self) -> _Compiled:
        tok = self._peek()
        if tok is None:
            raise _ParseError("unexpected end of expression")
        kind, value = tok
        if kind == "num":
            self._next()
            v = float(value)  # type: ignore[arg-type]
            return cast(_Compiled, lambda env, _v=v: _v)
        if kind == "(":
            self._next()
            inner = self._add()
            close = self._peek()
            if not close or close[0] != ")":
                raise _ParseError("missing closing parenthesis")
            self._next()
            return inner
        if kind == "name":
            self._next()
            name = str(value)
            nxt = self._peek()
            if nxt and nxt[0] == "(" and name in _UNARY_FUNCS:
                self._next()  # consume '('
                arg = self._add()
                close = self._peek()
                if not close or close[0] != ")":
                    raise _ParseError(f"missing ')' after {name}(")
                self._next()
                fn = _UNARY_FUNCS[name]
                return cast(_Compiled, lambda env, _fn=fn, _arg=arg: _fn(_arg(env)))
            if name in _CONSTANTS:
                const = _CONSTANTS[name]
                return cast(_Compiled, lambda env, _c=const: _c)
            if name in _UNARY_FUNCS:
                raise _ParseError(f"function {name!r} used without arguments")
            # A bare identifier is a free variable.
            self.free_vars.add(name)
            return cast(_Compiled, lambda env, _n=name: env[_n])
        raise _ParseError(f"unexpected token {kind!r}")

    @staticmethod
    def _binop(op: str, left: _Compiled, right: _Compiled) -> _Compiled:
        if op == "+":
            return lambda env: left(env) + right(env)
        if op == "-":
            return lambda env: left(env) - right(env)
        if op == "*":
            return lambda env: left(env) * right(env)
        if op == "/":
            return lambda env: left(env) / right(env)
        raise _ParseError(f"unknown operator {op!r}")  # pragma: no cover


def _compile(src: str) -> Tuple[_Compiled, Set[str]]:
    """Parse ``src`` into ``(callable, free_variable_names)``.

    Raises :class:`_ParseError` on any malformed input.
    """
    parser = _Parser(_tokenise(src))
    fn = parser.parse()
    return fn, parser.free_vars


# --------------------------------------------------------------------------- #
# Numeric-probing equivalence
# --------------------------------------------------------------------------- #

# Deterministic seed so a given pair of lines always yields the same verdict.
_PROBE_SEED = 1_618_033
# How many sample points we *want* to agree on before declaring equivalence.
_REQUIRED_SAMPLES = 24
# How many draws we are willing to attempt to reach that many valid samples
# (some draws hit singularities — sqrt of a negative, division by zero, …).
_MAX_DRAWS = 400
# Relative + absolute tolerance for "the two values are equal".
_REL_TOL = 1e-6
_ABS_TOL = 1e-9
# Range from which sample values for each free variable are drawn.
_SAMPLE_LO = -7.0
_SAMPLE_HI = 7.0


def _values_close(a: float, b: float) -> bool:
    if math.isnan(a) or math.isnan(b) or math.isinf(a) or math.isinf(b):
        return False
    return math.isclose(a, b, rel_tol=_REL_TOL, abs_tol=_ABS_TOL)


def _sample_points(free_vars: List[str], rng: random.Random) -> List[Dict[str, float]]:
    """Yield up to ``_MAX_DRAWS`` random environments over ``free_vars``."""
    points: List[Dict[str, float]] = []
    for _ in range(_MAX_DRAWS):
        points.append({v: rng.uniform(_SAMPLE_LO, _SAMPLE_HI) for v in free_vars})
    return points


def are_expressions_equivalent(a: str, b: str) -> EquivalenceResult:
    """Decide whether two **expressions** are algebraically equivalent.

    Equivalent ⟺ they evaluate equally at every valid sample point over the
    *union* of their free variables. Constant expressions (no free variables)
    are compared at a single point.
    """
    try:
        fa, vars_a = _compile(a)
        fb, vars_b = _compile(b)
    except _ParseError as exc:
        return EquivalenceResult(False, "Could not parse a line.", error=str(exc))

    free = sorted(vars_a | vars_b)
    rng = random.Random(_PROBE_SEED)

    valid = 0
    if not free:
        # Both constant: a single evaluation settles it.
        try:
            va, vb = fa({}), fb({})
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            return EquivalenceResult(False, "A line is undefined.", error=str(exc))
        if _values_close(va, vb):
            return EquivalenceResult(True, "Both sides are equal constants.")
        return EquivalenceResult(False, f"The two sides differ ({va:g} vs {vb:g}).")

    for env in _sample_points(free, rng):
        try:
            va = fa(env)
            vb = fb(env)
        except (ValueError, ZeroDivisionError, OverflowError):
            continue  # singular sample — skip, draw another
        if math.isnan(va) or math.isnan(vb) or math.isinf(va) or math.isinf(vb):
            continue
        if not _values_close(va, vb):
            where = ", ".join(f"{k}={env[k]:.3g}" for k in free)
            return EquivalenceResult(False, f"The two sides differ at {where}.")
        valid += 1
        if valid >= _REQUIRED_SAMPLES:
            return EquivalenceResult(True, "Both sides match across all sampled values.")

    if valid == 0:
        return EquivalenceResult(
            False,
            "Could not evaluate the lines (no valid sample points).",
            error="all sample points were singular",
        )
    # Agreed on every valid sample we managed to draw, just fewer than the target.
    return EquivalenceResult(True, "Both sides match across all sampled values.")


def _split_equation(line: str) -> Tuple[str, str] | None:
    """Split ``L = R`` into ``(L, R)``; ``None`` if it isn't a single equation."""
    parts = line.split("=")
    if len(parts) != 2:
        return None
    lhs, rhs = parts[0].strip(), parts[1].strip()
    if not lhs or not rhs:
        return None
    return lhs, rhs


def are_equations_equivalent(a: str, b: str) -> EquivalenceResult:
    """Decide whether two **equations** ``L = R`` have the same solution set.

    Each equation is normalised to ``L - R`` (whose zero set is the solution
    set). The two are equivalent iff one normal form is a **non-zero constant
    multiple** of the other across all sampled points — capturing the legal
    moves of equation solving (add/subtract the same thing, multiply/divide both
    sides by a non-zero constant, rearrange). ``0 = 0`` is equivalent only to
    another identity.
    """
    split_a = _split_equation(a)
    split_b = _split_equation(b)
    if split_a is None or split_b is None:
        return EquivalenceResult(
            False,
            "A line is not a single equation.",
            error="expected exactly one '=' on each line",
        )

    # Normal form L - R, as an expression string, reusing the parser.
    norm_a = f"({split_a[0]}) - ({split_a[1]})"
    norm_b = f"({split_b[0]}) - ({split_b[1]})"
    try:
        fa, vars_a = _compile(norm_a)
        fb, vars_b = _compile(norm_b)
    except _ParseError as exc:
        return EquivalenceResult(False, "Could not parse a line.", error=str(exc))

    free = sorted(vars_a | vars_b)
    rng = random.Random(_PROBE_SEED)

    ratio: float | None = None
    a_all_zero = True
    b_all_zero = True
    valid = 0

    points = _sample_points(free, rng) if free else [{}]  # constant equations (e.g. ``2 = 2``) need one point
    for env in points:
        try:
            va = fa(env)
            vb = fb(env)
        except (ValueError, ZeroDivisionError, OverflowError):
            continue
        if any(map(lambda v: math.isnan(v) or math.isinf(v), (va, vb))):
            continue
        valid += 1

        za = math.isclose(va, 0.0, abs_tol=_ABS_TOL)
        zb = math.isclose(vb, 0.0, abs_tol=_ABS_TOL)
        a_all_zero = a_all_zero and za
        b_all_zero = b_all_zero and zb

        if not za and not zb:
            r = va / vb
            if ratio is None:
                ratio = r
            elif not math.isclose(ratio, r, rel_tol=_REL_TOL, abs_tol=_ABS_TOL):
                where = ", ".join(f"{k}={env[k]:.3g}" for k in free) or "the constants"
                return EquivalenceResult(False, f"These equations have different solutions (at {where}).")
        elif za != zb:
            # One side is zero where the other isn't → solution sets diverge.
            where = ", ".join(f"{k}={env[k]:.3g}" for k in free) or "a tested value"
            return EquivalenceResult(False, f"These equations have different solutions (at {where}).")
        if valid >= _REQUIRED_SAMPLES:
            break

    if valid == 0:
        return EquivalenceResult(
            False,
            "Could not evaluate the equations.",
            error="all sample points were singular",
        )
    if a_all_zero and b_all_zero:
        return EquivalenceResult(True, "Both are identities (always true).")
    if a_all_zero != b_all_zero:
        return EquivalenceResult(False, "These equations have different solutions.")
    if ratio is None or math.isclose(ratio, 0.0, abs_tol=_ABS_TOL):
        # Couldn't establish a non-zero proportionality constant.
        return EquivalenceResult(False, "These equations have different solutions.")
    return EquivalenceResult(True, "These equations have the same solution.")


def check_step(previous: str, current: str) -> EquivalenceResult:
    """Top-level entry: is ``current`` a valid algebraic step from ``previous``?

    Auto-detects the form. If **both** lines contain exactly one ``=`` they are
    compared as *equations* (same solution set); otherwise they are compared as
    bare *expressions* (equal everywhere). A mixed pair (one equation, one
    expression) is rejected with an ``error`` — the deterministic fallback.

    This never raises: every malformed input returns an ``EquivalenceResult``
    with ``equivalent=False`` and a populated ``error``.
    """
    if not isinstance(previous, str) or not isinstance(current, str):
        return EquivalenceResult(False, "A line was not text.", error="non-string input")
    prev, cur = previous.strip(), current.strip()
    if not prev or not cur:
        return EquivalenceResult(False, "A line was empty.", error="empty line")

    prev_is_eq = _split_equation(prev) is not None
    cur_is_eq = _split_equation(cur) is not None

    # A bare "=" count mismatch (e.g. two '=' signs) → treat as parse error.
    if previous.count("=") > 1 or current.count("=") > 1:
        return EquivalenceResult(
            False,
            "A line has more than one '='.",
            error="multiple '=' on a line",
        )

    if prev_is_eq and cur_is_eq:
        return are_equations_equivalent(prev, cur)
    if not prev_is_eq and not cur_is_eq:
        return are_expressions_equivalent(prev, cur)
    return EquivalenceResult(
        False,
        "One line is an equation and the other isn't.",
        error="cannot compare an equation with a bare expression",
    )
