"""M7-08: tests for the importer's expression-coverage scan and the extended
croupier allowlist that drives the unknown-name count toward a stable set.

The scanner is read-only: it walks every ``{{...}}`` token across all subparts
and reports identifiers that are neither declared sampled variables, allowlisted
constants (``_SAFE_CONSTS``), nor allowlisted functions (``_SAFE_FUNCS``).
"""

from io import StringIO
from pathlib import Path

import pytest

from django.core.management import call_command

from openshiksha.apps.api.croupier import _SAFE_CONSTS, _SAFE_FUNCS, safe_eval_expr
from openshiksha.apps.core.management.commands.import_cabinet_questions import _collect_unknown_names, _iter_expressions
from openshiksha.apps.core.models import Question

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cabinet_sample"
SOURCE = str(FIXTURE_DIR)


# ── Unknown-name collection ───────────────────────────────────────────────────


class TestCollectUnknownNames:
    def test_declared_variable_is_known(self):
        assert _collect_unknown_names("a + b", declared_vars={"a", "b"}) == []

    def test_allowlisted_constant_is_known(self):
        # pi_val / e_val are in _SAFE_CONSTS.
        assert _collect_unknown_names("pi_val * r * r", declared_vars={"r"}) == []

    def test_allowlisted_function_is_known(self):
        assert _collect_unknown_names("trunc(a * b, 2)", declared_vars={"a", "b"}) == []

    def test_undeclared_name_is_unknown(self):
        assert _collect_unknown_names("a + zzz", declared_vars={"a"}) == ["zzz"]

    def test_function_name_not_in_allowlist_is_unknown(self):
        # ``bogus`` is neither a declared var nor an allowlisted callable.
        assert _collect_unknown_names("bogus(a)", declared_vars={"a"}) == ["bogus"]

    def test_malformed_expression_yields_nothing(self):
        assert _collect_unknown_names("a + + ", declared_vars={"a"}) == []

    def test_newly_allowlisted_helpers_are_known(self):
        # The M7-08 additions: gcd / lcm / factorial / trig / log should all
        # be recognised so they never appear in the unknowns report.
        for expr in ("gcd(a, b)", "lcm(a, b)", "factorial(a)", "sin(radians(a))", "log10(a)"):
            assert _collect_unknown_names(expr, declared_vars={"a", "b"}) == [], expr


class TestIterExpressions:
    def test_collects_tokens_from_all_fields(self):
        fields = {
            "question_text": "value is {{a}}",
            "solution_text": "because {{b + 1}}",
            "hint_text": "recall {{c}}",
            "options": [{"key": "A", "text": "{{d}}"}],
            "correct_answer": {"type": "numeric", "answer": "{{a + d}}"},
        }
        exprs = list(_iter_expressions(fields))
        assert "a" in exprs
        assert "b + 1" in exprs
        assert "c" in exprs
        assert "d" in exprs
        assert "a + d" in exprs

    def test_no_tokens_returns_empty(self):
        fields = {"question_text": "plain text, no tokens", "correct_answer": {"answer": "5"}}
        assert list(_iter_expressions(fields)) == []


# ── Extended allowlist (croupier) ─────────────────────────────────────────────


class TestExtendedAllowlist:
    def test_new_constants_present(self):
        assert "pi" in _SAFE_CONSTS and "e" in _SAFE_CONSTS

    def test_new_functions_present(self):
        for name in ("gcd", "lcm", "factorial", "degrees", "radians", "log", "exp", "sin", "cos"):
            assert name in _SAFE_FUNCS, name

    def test_gcd_evaluates(self):
        assert safe_eval_expr("gcd(a, b)", {"a": 12, "b": 8}) == 4.0

    def test_factorial_evaluates(self):
        assert safe_eval_expr("factorial(a)", {"a": 5}) == 120.0

    def test_pi_constant_evaluates(self):
        assert abs(safe_eval_expr("pi", {}) - 3.14159) < 0.001


# ── Command --report-unknowns (read-only) ─────────────────────────────────────


@pytest.mark.django_db
class TestReportUnknownsCommand:
    def test_writes_nothing_to_db(self):
        out = StringIO()
        call_command(
            "import_cabinet_questions",
            source=SOURCE,
            report_unknowns=True,
            stdout=out,
            stderr=StringIO(),
        )
        assert Question.objects.count() == 0

    def test_reports_scan_summary(self):
        out = StringIO()
        call_command(
            "import_cabinet_questions",
            source=SOURCE,
            report_unknowns=True,
            stdout=out,
            stderr=StringIO(),
        )
        assert "scanned containers" in out.getvalue()
