"""
Croupier — deterministic MCQ option shuffling.

Phase 1: Shuffle MCQ option order per (student_id, subpart_id) using a
hash-based seed. Same student always sees the same order (deterministic),
different students see different orders (anti-cheating).

Phase 2 (future): Variable substitution for numeric/fill-blank questions.

Key principle:
- Options are shuffled, then RE-KEYED by position so "A" always means the
  first displayed option regardless of original storage order.
- The grader calls get_original_key() to reverse-map the student's submitted
  key back to the original storage key for comparison with correct_answer.

Example:
  Original options: [{key: A, text: "x=2"}, {key: B, text: "x=-2"}, ...]
  correct_answer["answer"] = "A"   (x=2 is correct)

  Shuffle for student 42 produces order [C, A, D, B]:
    Displayed as: [{key: A, text: "x=0"}, {key: B, text: "x=2"}, ...]
  Student selects "B".

  get_original_key(42, subpart_id, "B", original_options)
    → re-applies shuffle → position B → original key "A"
    → grader compares "A" == "A" → correct!
"""

import ast
import hashlib
import math
import operator as _op
import random
import re
from typing import Any, Callable

# Keys assigned by position after shuffling
_POSITION_KEYS = ["A", "B", "C", "D", "E", "F", "G", "H"]


def _make_seed(student_id: int, subpart_id: int) -> int:
    """Create a deterministic integer seed from (student_id, subpart_id)."""
    seed_str = f"{student_id}:{subpart_id}"
    return int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**32)


def shuffle_options_for_student(options: list[dict], student_id: int, subpart_id: int) -> list[dict]:
    """
    Shuffle options deterministically for a given student + subpart.

    Returns a new list where:
    - Items are reordered by the seeded shuffle
    - Keys are re-assigned by display position (first item → "A", etc.)

    Input/output format: [{"key": "A", "text": "..."}, ...]
    """
    if not options or len(options) <= 1:
        return options

    seed = _make_seed(student_id, subpart_id)
    rng = random.Random(seed)

    shuffled = list(options)
    rng.shuffle(shuffled)

    # Re-key by position so keys reflect display order
    return [
        {"key": _POSITION_KEYS[i], "text": item["text"]} for i, item in enumerate(shuffled) if i < len(_POSITION_KEYS)
    ]


def get_original_key(
    student_id: int,
    subpart_id: int,
    submitted_key: str,
    original_options: list[dict],
) -> str:
    """
    Reverse-map a submitted key (from shuffled view) to the original storage key.

    Used by the grader to compare the student's answer against correct_answer.

    If submitted_key is not found in the shuffled positions (e.g., invalid input),
    returns the submitted_key unchanged so grading fails gracefully.
    """
    if not original_options or len(original_options) <= 1:
        return submitted_key

    seed = _make_seed(student_id, subpart_id)
    rng = random.Random(seed)

    shuffled = list(original_options)
    rng.shuffle(shuffled)

    # submitted_key is a position key (A=index 0, B=index 1, ...)
    position_map = {_POSITION_KEYS[i]: shuffled[i]["key"] for i in range(len(shuffled))}
    return position_map.get(submitted_key, submitted_key)


# ── Phase 2: Variable Substitution ────────────────────────────────────────────


def _make_var_seed(student_id: int, subpart_id: int) -> int:
    """Distinct seed namespace for variable substitution (Phase 2)."""
    seed_str = f"{student_id}:{subpart_id}:vars"
    return int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**32)


def sample_variable_values(
    variable_constraints: dict,
    student_id: int,
    subpart_id: int,
) -> dict:
    """
    Sample variable values deterministically for a (student, subpart) pair.

    Returns {"a": 3, "b": 14} for the given constraints.
    Same inputs always produce the same output (reproducible at grading time).
    """
    seed = _make_var_seed(student_id, subpart_id)
    rng = random.Random(seed)
    values = {}
    for name, spec in variable_constraints.items():
        lo, hi = spec["min"], spec["max"]
        is_int = spec.get("integer", True)
        decimals = spec.get("decimals", 2)
        if is_int:
            values[name] = rng.randint(int(lo), int(hi))
        else:
            raw = rng.uniform(float(lo), float(hi))
            values[name] = round(raw, decimals)
    return values


# ── Token substitution (supports {{var}} AND {{<expression>}}) ──────────────

_TOKEN_RE = re.compile(r"\{\{([^{}]+)\}\}")


def _format_value(value) -> str:
    """Render an evaluated value as a string suitable for student-facing text."""
    if isinstance(value, bool):  # bool is a subclass of int — handle first
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        # Trim trailing zeros so 6.0000 -> 6, 3.1400 -> 3.14, 28.2743 -> 28.2743
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def substitute_variables(text: str, variable_values: dict) -> str:
    """
    Replace every ``{{...}}`` token in ``text`` with its evaluated value.

    - A bare identifier (``{{j}}``) maps directly to ``variable_values[j]``.
    - Anything else (``{{j*2}}``, ``{{trunc(pi_val*r*r, 2)}}``) is parsed and
      evaluated via the safe AST evaluator with the sampled values in scope.
    - A token that fails to evaluate is left intact rather than raising, so a
      single bad expression never blanks an entire question.

    Empty / None text returns unchanged.
    """
    if not text:
        return text or ""

    def _repl(match: "re.Match[str]") -> str:
        expr = match.group(1).strip()
        # Fast path: bare identifier with a sampled value.
        if expr.isidentifier() and expr in variable_values:
            return _format_value(variable_values[expr])
        # General path: evaluate as an expression.
        try:
            return _format_value(_eval_expression(expr, variable_values))
        except Exception:
            return match.group(0)

    return _TOKEN_RE.sub(_repl, text)


def substitute_variables_for_student(
    question_text: str,
    options: "list[dict] | None",
    variable_constraints: "dict | None",
    student_id: int,
    subpart_id: int,
) -> "tuple[str, list[dict] | None, dict]":
    """
    Apply variable substitution to question_text and options for a student.

    Returns (substituted_text, substituted_options, variable_values).
    variable_values must be passed to the grader to evaluate correct_answer expressions.
    If variable_constraints is None or empty, returns inputs unchanged.
    """
    if not variable_constraints:
        return question_text, options, {}

    variable_values = sample_variable_values(variable_constraints, student_id, subpart_id)
    subst_text = substitute_variables(question_text, variable_values)
    subst_options = None
    if options:
        subst_options = [
            {"key": opt["key"], "text": substitute_variables(opt["text"], variable_values)} for opt in options
        ]
    return subst_text, subst_options, variable_values


# ── Safe expression evaluator (for correct_answer evaluation at grading time) ──

# Explicit annotations so mypy sees dict-dispatch values as callable.
_SAFE_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: _op.add,
    ast.Sub: _op.sub,
    ast.Mult: _op.mul,
    ast.Div: _op.truediv,
    ast.Pow: _op.pow,
    ast.Mod: _op.mod,
    ast.FloorDiv: _op.floordiv,
}
_SAFE_UNARY_OPS: dict[type, Callable[[Any], Any]] = {ast.USub: _op.neg, ast.UAdd: _op.pos}

# Named constants Cabinet authors reference directly.
_SAFE_CONSTS: dict[str, float] = {
    "pi_val": math.pi,
    "e_val": math.e,
}


def _trunc(x, n=0):
    """Truncate toward zero to ``n`` decimal places (matches legacy `trunc`)."""
    factor = 10 ** int(n)
    return math.trunc(float(x) * factor) / factor


# Safe function calls. ``Decimal`` is a no-op pass-through because modern is
# float-native (legacy used decimal.Decimal for arbitrary precision; the small
# rounding differences are immaterial for student-facing display).
_SAFE_FUNCS: dict[str, Callable[..., Any]] = {
    "trunc": _trunc,
    "round": round,
    "abs": abs,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "floor": math.floor,
    "ceil": math.ceil,
    "Decimal": float,
    "int": int,
    "float": float,
    "pow": pow,
}


def _eval_ast_node(node, variable_values: dict | None = None):
    """Recursively evaluate an AST node against the supplied variable scope."""
    variable_values = variable_values or {}

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in variable_values:
            return variable_values[node.id]
        if node.id in _SAFE_CONSTS:
            return _SAFE_CONSTS[node.id]
        raise ValueError(f"unknown identifier {node.id!r}")
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BIN_OPS:
        return _SAFE_BIN_OPS[type(node.op)](
            _eval_ast_node(node.left, variable_values),
            _eval_ast_node(node.right, variable_values),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARY_OPS:
        return _SAFE_UNARY_OPS[type(node.op)](_eval_ast_node(node.operand, variable_values))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
        args = [_eval_ast_node(a, variable_values) for a in node.args]
        kwargs = {kw.arg: _eval_ast_node(kw.value, variable_values) for kw in node.keywords if kw.arg}
        return _SAFE_FUNCS[node.func.id](*args, **kwargs)

    raise ValueError(f"Unsafe or unsupported expression node: {type(node).__name__}")


def _eval_expression(expr: str, variable_values: dict):
    """Parse and evaluate a raw expression string against ``variable_values``."""
    tree = ast.parse(expr, mode="eval")
    return _eval_ast_node(tree.body, variable_values)


def safe_eval_expr(expr: str, variable_values: dict) -> float:
    """
    Safely evaluate an arithmetic expression string with variable substitution.

    Accepts both ``{{var}}`` style tokens and bare ``var`` references — the
    former are interpolated via ``substitute_variables`` first, the latter
    resolved at AST eval time. Beyond ``+ - * / ** % //`` (and unary +/-) the
    evaluator also accepts an allowlist of math helpers:
    ``trunc, round, abs, min, max, sqrt, floor, ceil, Decimal, int, float, pow``
    and constants ``pi_val, e_val`` (matches Cabinet author syntax).

    Raises ValueError for anything outside the allowlist.
    """
    interpolated = substitute_variables(expr, variable_values)
    return float(_eval_expression(interpolated, variable_values))
