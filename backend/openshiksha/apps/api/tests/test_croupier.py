"""
Tests for Croupier Phase 1: deterministic MCQ option shuffling.

Validates:
- shuffle_options_for_student: same student → same order (deterministic)
- shuffle_options_for_student: different students → different orders (anti-cheating)
- get_original_key: reverse-maps submitted key back to original storage key
- Grading still correct when student submits the shuffled-position key
"""

from openshiksha.apps.api.croupier import get_original_key, shuffle_options_for_student

ORIGINAL_OPTIONS = [
    {"key": "A", "text": "x = 2"},
    {"key": "B", "text": "x = -2"},
    {"key": "C", "text": "x = 0"},
    {"key": "D", "text": "x = 4"},
]


class TestShuffleOptionsDeterminism:
    def test_same_student_same_subpart_deterministic(self):
        result1 = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=42, subpart_id=7)
        result2 = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=42, subpart_id=7)
        assert result1 == result2

    def test_different_students_different_order(self):
        result1 = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=1, subpart_id=7)
        result2 = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=2, subpart_id=7)
        # With 4 options there are 24 permutations — extremely unlikely to match by chance
        texts1 = [o["text"] for o in result1]
        texts2 = [o["text"] for o in result2]
        assert texts1 != texts2, "Two different students got identical MCQ order — seed collision"

    def test_shuffled_options_contain_all_original_texts(self):
        result = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=99, subpart_id=3)
        original_texts = {o["text"] for o in ORIGINAL_OPTIONS}
        shuffled_texts = {o["text"] for o in result}
        assert original_texts == shuffled_texts

    def test_shuffled_keys_are_reassigned_by_position(self):
        result = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=5, subpart_id=1)
        # Keys should be A, B, C, D in order (reassigned by position)
        assert [o["key"] for o in result] == ["A", "B", "C", "D"]

    def test_single_option_unchanged(self):
        single = [{"key": "A", "text": "only one"}]
        result = shuffle_options_for_student(single, student_id=1, subpart_id=1)
        assert result == single

    def test_empty_options_unchanged(self):
        result = shuffle_options_for_student([], student_id=1, subpart_id=1)
        assert result == []


class TestGetOriginalKey:
    def test_reverse_maps_position_key_to_original(self):
        shuffled = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=42, subpart_id=7)
        # For each position in the shuffled result, the text at that position
        # should match the original option whose key is returned by get_original_key
        for shuffled_option in shuffled:
            position_key = shuffled_option["key"]
            original_key = get_original_key(42, 7, position_key, ORIGINAL_OPTIONS)
            original_option = next(o for o in ORIGINAL_OPTIONS if o["key"] == original_key)
            assert original_option["text"] == shuffled_option["text"], (
                f"Position {position_key} maps to original {original_key} "
                f"but texts don't match: '{shuffled_option['text']}' vs '{original_option['text']}'"
            )

    def test_correct_answer_survives_shuffle_and_reverse(self):
        """Simulate the full grading flow: correct_answer='A', student sees shuffle, submits shuffled key."""
        correct_original_key = "A"  # "x = 2" is correct

        shuffled = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=42, subpart_id=7)

        # Student sees the shuffled options; find where "x = 2" ended up
        displayed_key_for_correct = next(o["key"] for o in shuffled if o["text"] == "x = 2")

        # Student submits that displayed key
        submitted_key = displayed_key_for_correct

        # Grader reverses the shuffle
        resolved_key = get_original_key(42, 7, submitted_key, ORIGINAL_OPTIONS)

        assert resolved_key == correct_original_key

    def test_invalid_submitted_key_returns_unchanged(self):
        """If student submits a key that doesn't exist, return it unchanged (grading fails gracefully)."""
        result = get_original_key(42, 7, "Z", ORIGINAL_OPTIONS)
        assert result == "Z"

    def test_single_option_passthrough(self):
        single = [{"key": "A", "text": "only"}]
        result = get_original_key(1, 1, "A", single)
        assert result == "A"


class TestGradeSubpartWithCroupier:
    """Integration: _grade_subpart with croupier reverse-mapping."""

    def test_mcq_graded_correctly_after_shuffle(self):
        from openshiksha.apps.core.tasks import _grade_subpart

        correct_answer = {"type": "mcq", "answer": "A"}  # "x = 2" is correct

        shuffled = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=42, subpart_id=7)

        # Find where the correct option ("x = 2") ended up in the student's view
        student_submitted_key = next(o["key"] for o in shuffled if o["text"] == "x = 2")

        mark = _grade_subpart(
            "mcq",
            student_submitted_key,
            correct_answer,
            student_id=42,
            subpart_id=7,
            original_options=ORIGINAL_OPTIONS,
        )
        assert mark == 1.0

    def test_mcq_wrong_answer_scores_zero(self):
        from openshiksha.apps.core.tasks import _grade_subpart

        correct_answer = {"type": "mcq", "answer": "A"}  # "x = 2" is correct

        shuffled = shuffle_options_for_student(ORIGINAL_OPTIONS, student_id=42, subpart_id=7)

        # Student picks the wrong option (not x=2)
        wrong_key = next(o["key"] for o in shuffled if o["text"] != "x = 2")

        mark = _grade_subpart(
            "mcq",
            wrong_key,
            correct_answer,
            student_id=42,
            subpart_id=7,
            original_options=ORIGINAL_OPTIONS,
        )
        assert mark == 0.0

    def test_non_mcq_not_affected_by_croupier(self):
        from openshiksha.apps.core.tasks import _grade_subpart

        mark = _grade_subpart("numeric", "42", {"type": "numeric", "answer": "42"})
        assert mark == 1.0
