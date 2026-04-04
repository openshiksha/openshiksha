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

import hashlib
import random

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
