"""Tests for the M7-07 shared-stem extraction in import_cabinet_questions."""

from openshiksha.apps.core.management.commands.import_cabinet_questions import (
    _lift_shared_stem,
    _split_leading_paragraph,
)


class TestSplitLeadingParagraph:
    def test_empty(self):
        assert _split_leading_paragraph("") == ("", "")

    def test_no_paragraph(self):
        assert _split_leading_paragraph("Just a single line.") == ("", "Just a single line.")

    def test_html_p_tag(self):
        head, tail = _split_leading_paragraph("<p>Read this first.</p>Then the rest.")
        assert head == "<p>Read this first.</p>"
        assert tail == "Then the rest."

    def test_double_newline_split(self):
        head, tail = _split_leading_paragraph("Setup paragraph here.\n\nSubpart prompt.")
        assert head == "Setup paragraph here."
        assert tail == "Subpart prompt."

    def test_leading_whitespace_tolerated(self):
        head, _tail = _split_leading_paragraph("   <p>hello</p>world")
        assert head == "<p>hello</p>"


class TestLiftSharedStem:
    def test_single_subpart_never_lifts(self):
        subparts = [{"question_text": "<p>Long shared stem here, lots of words.</p>Q1"}]
        assert _lift_shared_stem(subparts) == ""
        # And the subpart is left untouched.
        assert subparts[0]["question_text"] == "<p>Long shared stem here, lots of words.</p>Q1"

    def test_lifts_identical_html_paragraph(self):
        stem = "<p>Consider the polynomial f(x) = x^2 + 3x + 2.</p>"
        subparts = [
            {"question_text": f"{stem}Find the roots."},
            {"question_text": f"{stem}Find the vertex."},
        ]
        lifted = _lift_shared_stem(subparts)
        assert lifted == stem
        assert subparts[0]["question_text"] == "Find the roots."
        assert subparts[1]["question_text"] == "Find the vertex."

    def test_does_not_lift_when_heads_differ(self):
        subparts = [
            {"question_text": "<p>Different stem A here friend.</p>Tail A."},
            {"question_text": "<p>Different stem B here friend.</p>Tail B."},
        ]
        assert _lift_shared_stem(subparts) == ""
        # Subparts untouched on no-lift.
        assert subparts[0]["question_text"].startswith("<p>Different stem A")

    def test_does_not_lift_short_stem(self):
        # Below the 20-char threshold: looks like a label, not a stem.
        subparts = [
            {"question_text": "<p>Q.</p>real one"},
            {"question_text": "<p>Q.</p>real two"},
        ]
        assert _lift_shared_stem(subparts) == ""

    def test_no_paragraph_no_lift(self):
        subparts = [
            {"question_text": "first plain line"},
            {"question_text": "second plain line"},
        ]
        assert _lift_shared_stem(subparts) == ""
