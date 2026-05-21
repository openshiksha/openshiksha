"""
Edge models — Analytics and Proficiency Tracking

Modern implementation of the analytics engine.

Legacy reference: edge/models.py
Improvements over legacy:
- Tick FK to QuestionSubpart (not Question) — enables per-subpart proficiency
- Tick has submission FK — full traceability back to student answers
- Tick has created_at — enables time-decay weighting in future algorithm improvements
- StudentProficiency uses update_fields — avoids full row writes under concurrent updates
- All FKs snake_case (legacy used camelCase: subjectRoom, questiontag)
- unique_together on SubjectRoomProficiency (questiontag + subjectroom)
- SubjectRoomQuestionMistake.apply_tick() accepts num_subparts to avoid N+1 query
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

FRACTION_VALIDATOR = [MinValueValidator(0.0), MaxValueValidator(1.0)]

# Import from core only inside methods to avoid circular imports at class definition time
# (edge -> core is fine; core -> edge must be avoided at module level)


class Tick(models.Model):
    """
    Records the result of grading a single question subpart in a submission.

    Legacy: same concept. Improved: FK to QuestionSubpart (not Question),
    submission FK for traceability, created_at for temporal analytics.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="ticks",
        limit_choices_to={"role__in": ["student", "open_student"]},
        help_text="The student whose answer resulted in this tick",
    )
    question_subpart = models.ForeignKey(
        "core.QuestionSubpart",
        on_delete=models.CASCADE,
        related_name="ticks",
        help_text="The question subpart that was answered",
    )
    submission = models.ForeignKey(
        "core.Submission",
        on_delete=models.CASCADE,
        related_name="ticks",
        help_text="The submission this tick came from",
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="ticks",
        help_text="The SubjectRoom whose assignment produced this tick",
    )
    mark = models.FloatField(
        validators=FRACTION_VALIDATOR, help_text="Mark obtained for this subpart (fraction 0.0–1.0)"
    )
    is_acknowledged = models.BooleanField(
        default=False, help_text="Whether this tick has been factored into proficiency calculations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "subject_room"]),
            models.Index(fields=["is_acknowledged"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Tick: {self.student} | subpart {self.question_subpart_id} | mark={self.mark}"

    def acknowledge(self):
        """Mark this tick as factored into proficiency."""
        self.is_acknowledged = True
        self.save(update_fields=["is_acknowledged"])


class StudentProficiency(models.Model):
    """
    Tracks a student's proficiency in a specific QuestionTag within a SubjectRoom.

    Score formula (preserved from legacy): score = (0.7 × rate) + (0.3 × percentile)
    - rate: student's rolling average mark for this tag
    - percentile: how they rank vs classmates in the same SubjectRoom + tag

    Improvements over legacy:
    - update_fields on all saves (legacy used full save() — caused race conditions)
    - updated_at for cache invalidation
    - renamed total → total_marks, ticks → tick_count for clarity
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="proficiencies",
        help_text="The student whose proficiency is tracked",
    )
    question_tag = models.ForeignKey(
        "core.QuestionTag",
        on_delete=models.CASCADE,
        related_name="student_proficiencies",
        help_text="The tag that this proficiency is calculated in",
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="student_proficiencies",
        help_text="The SubjectRoom in which this proficiency applies",
    )

    # Accumulated tick state
    total_marks = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Cumulative marks obtained across all ticks in this tag",
    )
    tick_count = models.PositiveIntegerField(default=0, help_text="Number of ticks this proficiency is calculated over")

    # Derived scores
    rate = models.FloatField(
        default=0.0, validators=FRACTION_VALIDATOR, help_text="Average mark in this tag (total_marks / tick_count)"
    )
    percentile = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="Percentile rank within this SubjectRoom and tag (0.0–1.0)",
    )
    score = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="Final proficiency score: (0.7 × rate) + (0.3 × percentile)",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["student", "question_tag", "subject_room"]]
        indexes = [
            models.Index(fields=["subject_room", "question_tag"]),
            models.Index(fields=["student", "score"]),
        ]

    def __str__(self):
        return f"Proficiency: {self.student} | {self.question_tag} | score={self.score:.2f}"

    def apply_tick(self, tick: "Tick") -> None:
        """
        Update rate from a new tick. Does NOT recalculate percentile or final score —
        call recalculate_score() separately after percentile is updated.
        """
        self.tick_count += 1
        self.total_marks += tick.mark
        self.rate = self.total_marks / self.tick_count
        self.save(update_fields=["tick_count", "total_marks", "rate", "updated_at"])

    def recalculate_score(self, percentile: float) -> None:
        """Set percentile and recompute final score using the legacy formula."""
        self.percentile = percentile
        self.score = (0.7 * self.rate) + (0.3 * self.percentile)
        self.save(update_fields=["percentile", "score", "updated_at"])

    @staticmethod
    def calculate_score(rate: float, percentile: float) -> float:
        """Static helper to compute score without an instance."""
        return (0.7 * rate) + (0.3 * percentile)


class StudentProficiencySnapshot(models.Model):
    """
    Append-only record written every time StudentProficiency is recalculated.

    Never updated — always inserted. Preserves full trend history even if the
    live StudentProficiency record is later deleted or the student moves rooms.
    Keyed on (student, question_tag, subject_room) for simple filtering.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="proficiency_snapshots",
    )
    question_tag = models.ForeignKey(
        "core.QuestionTag",
        on_delete=models.CASCADE,
        related_name="proficiency_snapshots",
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="proficiency_snapshots",
    )
    score = models.FloatField(help_text="Snapshot of score at this point in time (0.0–1.0)")
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["recorded_at"]
        indexes = [
            models.Index(fields=["student", "question_tag", "subject_room", "recorded_at"]),
        ]

    def __str__(self):
        return (
            f"Snapshot({self.student_id}, tag={self.question_tag_id},"
            f" score={self.score:.2f}, at={self.recorded_at.date()})"
        )


class SubjectRoomProficiency(models.Model):
    """
    Average proficiency of all students in a SubjectRoom for a given tag.
    Used for percentile calculation and teacher-facing analytics dashboards.

    Legacy: same concept. Improved: unique_together enforced (legacy had none).
    """

    question_tag = models.ForeignKey(
        "core.QuestionTag",
        on_delete=models.CASCADE,
        related_name="subjectroom_proficiencies",
        help_text="The tag that this class-level proficiency is calculated in",
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="subjectroom_proficiencies",
        help_text="The SubjectRoom for which aggregate proficiency is tracked",
    )
    rate = models.FloatField(default=0.0, validators=FRACTION_VALIDATOR)
    percentile = models.FloatField(default=0.0, validators=FRACTION_VALIDATOR)
    score = models.FloatField(default=0.0, validators=FRACTION_VALIDATOR)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["question_tag", "subject_room"]]

    def __str__(self):
        return f"RoomProficiency: {self.subject_room} | {self.question_tag} | score={self.score:.2f}"

    def update(self, rate: float, percentile: float) -> None:
        self.rate = rate
        self.percentile = percentile
        self.score = StudentProficiency.calculate_score(rate, percentile)
        self.save(update_fields=["rate", "percentile", "score", "updated_at"])


class SubjectRoomQuestionMistake(models.Model):
    """
    Aggregates marks lost for a specific question across a SubjectRoom.
    Teachers can use this to identify which questions caused the most difficulty.

    Legacy: same concept. Improved: apply_tick() accepts num_subparts to avoid
    calling question.get_num_subparts() on every tick (was an N+1 in legacy).
    """

    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="question_mistakes",
        help_text="The SubjectRoom whose students made the mistakes",
    )
    question = models.ForeignKey(
        "core.Question",
        on_delete=models.CASCADE,
        related_name="question_mistakes",
        help_text="The question for which incorrect answers are aggregated",
    )
    regression = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Cumulative marks lost (absolute, not fraction) — higher = harder question for this class",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["subject_room", "question"]]

    def __str__(self):
        return f"Mistake: {self.subject_room} | Q{self.question_id} | regression={self.regression:.2f}"

    def apply_tick(self, tick: "Tick", num_subparts: int) -> None:
        """
        Accumulate marks lost from a single tick.
        num_subparts must be pre-fetched to avoid N+1 queries.
        """
        if num_subparts > 0:
            self.regression += (1.0 - tick.mark) / num_subparts
            self.save(update_fields=["regression", "updated_at"])
