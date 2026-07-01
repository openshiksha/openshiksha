"""
Deterministic *propose-and-verify* problem verifier — the Phase 3 correctness
keystone (the counterpart to DTB-1's ``validate_widget_config`` and GSV-1's
``check_step``).

Phase 3 of the AI-Native Interactive Learning initiative builds a
*propose-and-verify practice bank*: the AI **proposes** a widget problem
(``widget_kind`` + ``widget_config`` + the question's ``correct_answer``), and a
**deterministic engine confirms the problem is well-posed and the expected
answer is actually reachable** *before anything ships*. **AI proposes, the engine
disposes** — correctness is, and stays, deterministic. No LLM is consulted here.

The load-bearing property this module enforces is **answer reachability**: for an
*answer-producing* widget the student can only report values the widget can
actually emit, so a ``correct_answer`` the widget can never produce is an
**ill-posed problem** — the student literally cannot mark the right answer and
would be graded wrong no matter what. The `number-line` widget makes this
concrete (and is the proven trickiest case): it snaps the dragged point to its
``step`` grid and rounds to ``decimals = max(0, -floor(log10(step)))`` decimals,
so e.g. with ``step 0.25`` the value ``0.75`` rounds to ``0.8`` and is
**unreachable** (the exact bug DTB-4 hit with ¾). This verifier reproduces that
snap **faithfully** (a host-side port of
``frontend_modern/src/widgets/number-line/index.ts``, mirror-disciplined the way
``algebra.py`` ↔ ``algebra.ts`` are) and ties "reachable" to the **same numeric
tolerance the grader uses** (``apps.core.tasks._grade_subpart``) — so a problem
this engine passes is one the real grader can actually mark correct.

Iron-clad bar this increment meets:

* **AI nowhere near it** — pure deterministic verification (principle #2).
* **Grounded** — reuses DTB-1 ``is_valid_widget_config`` + the kind's vendored
  schema, the croupier's own variable sampler, and the grader's tolerance, so it
  reasons about the *real* answer space, never an imagined one (principle #5).
* **Deterministic fallback, never a 500** — every malformed input degrades to a
  structured :class:`ProblemVerdict` with ``ok=False`` and a reason; this module
  never raises (principle #4).

Later Phase-3 increments ride on this: PV-2 (``/ai/practice-problem/`` endpoint)
will only ever return a problem this verifier has passed; the repair/fallback
path mirrors DTB-2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from .widgets import is_valid_widget_config

# Widgets that route the student's interaction into the answer via
# ``ctx.reportValue`` — for these the widget *constrains* the answer space, so
# reachability is verifiable. Mirrors ``meta.answerProducing`` in the frontend
# registry; today only ``number-line``. Explanatory kinds (fraction-bar,
# function-plotter, thermo-piston) let the student answer in the free field, so
# the widget does not bound the answer and there is nothing on a grid to verify.
ANSWER_PRODUCING_WIDGET_KINDS: tuple[str, ...] = ("number-line",)

# Grader tolerances, copied to stay in lock-step with
# ``apps.core.tasks._grade_subpart``: a literal numeric answer is marked correct
# within 1e-3; a per-student variable answer within 1e-2. "Reachable" means the
# widget can emit a value the grader would accept, so we reuse the same bands.
_LITERAL_TOL = 0.001
_VARIABLE_TOL = 0.01

# How many synthetic students to sample when checking a variable-aware problem is
# well-posed for *everyone*, not just nominally. Deterministic (fixed ids), so
# the verdict is reproducible and unit-testable with zero DB.
_DEFAULT_SAMPLE_SIZE = 8


@dataclass(frozen=True)
class ProblemVerdict:
    """Structured result of :func:`verify_widget_problem` (never an exception).

    ``ok`` is the ship/no-ship signal. ``code`` is a stable machine label (see the
    module-level outcomes); ``reason`` is a teacher-readable sentence; ``details``
    carries supporting values (e.g. ``nearest_reachable``) for the UI/tests.
    """

    ok: bool
    code: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:  # so callers can write ``if verdict:``
        return self.ok


def _as_number(value: Any) -> Optional[float]:
    """Coerce a literal numeric answer to ``float``; ``None`` if not numeric.

    Accepts ints/floats and numeric strings (``"0.75"``) — the grader compares via
    ``float(...)`` — but rejects bools (``True`` is not an answer) and anything
    that won't parse. A ``{{var}}`` expression is *not* a literal and returns
    ``None`` (the caller routes those to the variable-aware path).
    """

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _number_line_params(config: dict) -> tuple[float, float, float]:
    """``(min, max, step)`` with the **same defaults the widget applies**.

    Mirrors ``frontend_modern/src/widgets/number-line/index.ts``: a non-finite or
    absent field falls back to its default, and a non-positive ``step`` falls back
    to 1 (the widget's ``Number.isFinite(step) && step > 0`` guard).
    """

    def num(key: str, default: float) -> float:
        v = config.get(key, default)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return default
        f = float(v)
        return f if math.isfinite(f) else default

    lo = num("min", 0.0)
    hi = num("max", 10.0)
    step = num("step", 1.0)
    if step <= 0:
        step = 1.0
    return lo, hi, step


def _snap_number_line(value: float, lo: float, hi: float, step: float) -> float:
    """Faithful host-side port of the number-line widget's ``snap``.

    Snaps to the ``step`` grid anchored at ``lo``, clamps into ``[lo, hi]``, and
    rounds to ``decimals = max(0, -floor(log10(step)))`` — the exact arithmetic in
    the widget, so what this returns is precisely what the student would report.
    """

    snapped = round((value - lo) / step) * step + lo
    clamped = max(lo, min(hi, snapped))
    decimals = max(0, -math.floor(math.log10(step)))
    return round(clamped, decimals)


def _reachable_on_number_line(answer: float, config: dict, tol: float) -> tuple[bool, float]:
    """Is ``answer`` a value the number-line can actually emit?

    Returns ``(reachable, nearest_reachable)``. Reachable iff snapping ``answer``
    reproduces it within the grader's tolerance — which catches both
    off-the-grid answers (``0.75`` with ``step 0.25`` → ``0.8``) and
    out-of-``[min, max]`` answers (clamping moves them).
    """

    lo, hi, step = _number_line_params(config)
    nearest = _snap_number_line(answer, lo, hi, step)
    return abs(nearest - answer) < tol, nearest


def _verify_literal(kind: str, config: dict, answer_raw: Any) -> ProblemVerdict:
    """Reachability check for a literal (non-variable) answer."""

    answer = _as_number(answer_raw)
    if answer is None:
        return ProblemVerdict(
            ok=False,
            code="answer_not_numeric",
            reason=(
                f"The {kind} widget reports a numeric answer, but the "
                f"correct answer {answer_raw!r} is not a number."
            ),
            details={"answer": answer_raw},
        )

    reachable, nearest = _reachable_on_number_line(answer, config, _LITERAL_TOL)
    if reachable:
        return ProblemVerdict(
            ok=True,
            code="ok",
            reason="The correct answer is reachable on the widget.",
            details={"answer": answer, "nearest_reachable": nearest},
        )
    return ProblemVerdict(
        ok=False,
        code="unreachable",
        reason=(
            f"The answer {answer} cannot be marked on this {kind}: the closest "
            f"value the student can reach is {nearest}. Adjust the range/step (or "
            f"the answer) so the answer lands on the grid."
        ),
        details={"answer": answer, "nearest_reachable": nearest},
    )


def _verify_variable(
    kind: str,
    config: dict,
    answer_raw: Any,
    variable_constraints: dict,
    sample_size: int,
) -> ProblemVerdict:
    """Reachability check for a ``{{var}}`` answer, across sampled students.

    Confirms the problem is well-posed for *every* student, not just on paper: for
    each of ``sample_size`` deterministic synthetic students we sample the
    variables exactly as the croupier will at grade time, evaluate the answer
    expression, and require it to be reachable on the widget. A single
    unreachable sample fails the whole problem (it would be impossible for that
    student). Reuses the croupier's own sampler/evaluator so the verifier and the
    runtime can't drift.
    """

    # Lazy import to avoid a core→api layer inversion at module load (the same
    # pattern apps.core.tasks uses to reach the croupier).
    from openshiksha.apps.api.croupier import safe_eval_expr, sample_variable_values

    answer_str = str(answer_raw)
    for student_id in range(1, sample_size + 1):
        subpart_id = 1  # fixed → the (student, subpart) seed varies by student
        values: dict = {}
        try:
            values = sample_variable_values(variable_constraints, student_id, subpart_id)
            expected = safe_eval_expr(answer_str, values)
        except (ValueError, ZeroDivisionError, KeyError, TypeError, SyntaxError):
            return ProblemVerdict(
                ok=False,
                code="answer_not_numeric",
                reason=(
                    f"The answer expression {answer_raw!r} could not be evaluated "
                    f"for the sampled variables {values}."
                ),
                details={"answer": answer_raw},
            )
        if not math.isfinite(expected):
            return ProblemVerdict(
                ok=False,
                code="answer_not_numeric",
                reason=f"The answer expression {answer_raw!r} evaluated to a non-finite value.",
                details={"answer": answer_raw},
            )
        reachable, nearest = _reachable_on_number_line(expected, config, _VARIABLE_TOL)
        if not reachable:
            return ProblemVerdict(
                ok=False,
                code="unreachable_for_some",
                reason=(
                    f"For some students the correct answer ({expected}) cannot be "
                    f"marked on this {kind} — the closest reachable value is "
                    f"{nearest}. The randomized range can produce answers off the "
                    f"widget's grid."
                ),
                details={
                    "answer": expected,
                    "nearest_reachable": nearest,
                    "variable_values": values,
                },
            )
    return ProblemVerdict(
        ok=True,
        code="ok_variable",
        reason=f"The correct answer is reachable for all {sample_size} sampled students.",
        details={"sample_size": sample_size},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Propose-and-verify guardrail support (PV-2)
#
# PV-2's ``/ai/practice-problem/`` endpoint proposes a widget problem with an LLM
# and must *never* ship one this engine can't pass. The two deterministic,
# LLM-free helpers below are what the AI proposer rides on — exactly as DTB-2 rode
# on ``repair_widget_config`` + ``SAFE_DEFAULT_CONFIGS``:
#
#   * :data:`SAFE_DEFAULT_PROBLEM` — a known-reachable ``number-line`` problem, the
#     fallback when no LLM is available or its proposal can't be salvaged.
#   * :func:`snap_literal_answer` — a bounded deterministic repair that moves a
#     proposed literal answer onto the widget's own grid (reusing the same snap
#     this module ports), so a slightly-off answer becomes reachable instead of
#     failing the whole problem. Reachability after the snap is guaranteed because
#     the snap is idempotent — snapping the snapped value reproduces it.
#
# None of this calls an LLM; it is the deterministic core PV-2 layers the proposer
# on top of (principles #3 validate-before-store and #4 deterministic fallback).
# ─────────────────────────────────────────────────────────────────────────────

# A known-good, reachable ``number-line`` problem. Used as the deterministic
# fallback when the LLM is unavailable or its proposal can't be verified/repaired
# — always a well-posed problem, never a 500 and never a stub shown as real (the
# caller flags provenance honestly). Verified reachable by the test-suite.
SAFE_DEFAULT_PROBLEM: dict[str, Any] = {
    "widget_kind": "number-line",
    "widget_config": {"min": 0, "max": 10, "step": 1, "label": "Mark the value"},
    "correct_answer": {"answer": 7},
}


def snap_literal_answer(kind: str, config: Any, correct_answer: Any) -> Optional[dict]:
    """Deterministically move a literal numeric answer onto the widget's grid.

    Returns a repaired ``correct_answer`` dict whose ``answer`` is a value the
    widget can actually emit (so :func:`verify_widget_problem` will then pass), or
    ``None`` when there is nothing deterministic to repair: a non-answer-producing
    kind, a missing/non-numeric answer, or a ``{{var}}`` expression (whose
    per-student reachability can't be fixed by snapping a single value).

    Reuses the module's own faithful port of the widget snap, so the returned
    value is exactly what the student would report — and snapping is idempotent,
    so the repaired answer is guaranteed reachable.
    """

    if kind not in ANSWER_PRODUCING_WIDGET_KINDS:
        return None
    if not isinstance(correct_answer, dict) or "answer" not in correct_answer:
        return None
    answer = _as_number(correct_answer["answer"])
    if answer is None:
        return None
    cfg = config if isinstance(config, dict) else {}
    lo, hi, step = _number_line_params(cfg)
    snapped = _snap_number_line(answer, lo, hi, step)
    return {**correct_answer, "answer": snapped}


def verify_widget_problem(
    kind: str,
    config: Any,
    correct_answer: Any,
    *,
    variable_constraints: Any = None,
    sample_size: int = _DEFAULT_SAMPLE_SIZE,
) -> ProblemVerdict:
    """Confirm a proposed widget *problem* is well-posed and answerable.

    The Phase-3 keystone: given a ``widget_kind`` + ``widget_config`` + the
    question's ``correct_answer`` (and, for randomized problems, the
    ``variable_constraints`` the croupier will sample), return a structured
    :class:`ProblemVerdict` saying whether the problem may ship. Checks, in order:

    1. **Config is schema-valid** (DTB-1 ``is_valid_widget_config``).
    2. **The answer is present** (``correct_answer`` is a dict with ``"answer"``).
    3. **The answer is reachable on the widget** — for an *answer-producing* kind,
       the value (or, with constraints, every sampled student's value) must be a
       value the widget can actually emit. Explanatory kinds have no widget-bound
       answer space, so step 3 is a no-op (``ok``, ``code="ok_explanatory"``).

    Never raises — any malformed input is a deterministic ``ok=False`` verdict.
    """

    if not is_valid_widget_config(kind, config):
        return ProblemVerdict(
            ok=False,
            code="invalid_config",
            reason=f"The {kind or 'widget'} config is not valid against its schema.",
            details={},
        )

    if not isinstance(correct_answer, dict) or "answer" not in correct_answer:
        return ProblemVerdict(
            ok=False,
            code="no_answer",
            reason="The problem has no correct_answer to verify.",
            details={},
        )

    # Explanatory widgets don't constrain the answer field — nothing on a grid to
    # check. We honestly verify only what the widget actually bounds.
    if kind not in ANSWER_PRODUCING_WIDGET_KINDS:
        return ProblemVerdict(
            ok=True,
            code="ok_explanatory",
            reason=f"The {kind} widget does not constrain the answer; config and answer are well-formed.",
            details={},
        )

    answer_raw = correct_answer["answer"]
    config_dict = config if isinstance(config, dict) else {}

    constraints = variable_constraints if isinstance(variable_constraints, dict) else None
    is_variable_answer = isinstance(answer_raw, str) and "{{" in answer_raw
    if constraints and is_variable_answer:
        size = sample_size if isinstance(sample_size, int) and sample_size > 0 else _DEFAULT_SAMPLE_SIZE
        return _verify_variable(kind, config_dict, answer_raw, constraints, size)

    return _verify_literal(kind, config_dict, answer_raw)
