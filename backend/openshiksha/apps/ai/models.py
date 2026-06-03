"""
AI Analytics models for OpenShiksha

Implements smart analytics and insights:
- LearningGap: Per-student weakness detection at chapter level
- ClassInsight: Aggregated class-level insight for teachers
- PerformancePrediction: Heuristic exam-readiness forecast per subject

AI-Powered Content Recommendations:
- ContentRecommendation: What a student should practice next (and why)
- PracticePlan: A daily bundle of recommendations for a student

Adaptive Learning Engine:
- KnowledgeNode: Chapter in the curriculum with prerequisite relationships
- StudentMastery: Per-student mastery level for a KnowledgeNode
- LearningPath: Personalised chapter sequence generated for a student
- LearningPathStep: Individual step within a LearningPath with status
- SpacedRepetitionEntry: SM-2-style review scheduling per student × chapter

All analytics are computed asynchronously via Celery tasks and cached here
for fast API reads. The source of truth is always the Tick + StudentProficiency
data in edge/; these models are derived views.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

FRACTION_VALIDATOR = [MinValueValidator(0.0), MaxValueValidator(1.0)]


# ─────────────────────────────────────────────────────────────────────────────
# Natural Language Explanations
# ─────────────────────────────────────────────────────────────────────────────


class ExplanationLanguage(models.TextChoices):
    ENGLISH = "en", "English"
    HINDI = "hi", "Hindi"


class SubpartExplanation(models.Model):
    """
    AI-generated explanation of why a student's answer was correct or incorrect.

    Generated asynchronously after grading. One per (student, subpart, submission).

    The explanation is grade-calibrated: simpler language for Std 1–6,
    intermediate for 7–9, and full complexity for 10–12.

    Stored persistently so students can revisit explanations without re-calling
    the LLM API. Each explanation records the model and token count for cost
    visibility.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="subpart_explanations",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    question_subpart = models.ForeignKey(
        "core.QuestionSubpart",
        on_delete=models.CASCADE,
        related_name="explanations",
    )
    submission = models.ForeignKey(
        "core.Submission",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="explanations",
        help_text="Null for SRS drill explanations not tied to a formal submission.",
    )

    student_answer = models.JSONField(
        help_text="The answer the student submitted (raw value, pre-croupier-reversal).",
    )
    is_correct = models.BooleanField(
        help_text="Whether the student's answer was graded as correct.",
    )
    explanation_text = models.TextField(
        help_text="AI-generated plain-language explanation (2–5 sentences).",
    )
    language = models.CharField(
        max_length=5,
        choices=ExplanationLanguage.choices,
        default=ExplanationLanguage.ENGLISH,
    )
    grade_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Grade level used to calibrate explanation complexity.",
    )

    model_used = models.CharField(
        max_length=60,
        default="claude-sonnet-4-6",
        help_text="LLM model ID that generated this explanation.",
    )
    input_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Prompt tokens consumed (for cost tracking).",
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Completion tokens produced (for cost tracking).",
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_subpart_explanations"
        unique_together = [["student", "question_subpart", "submission"]]
        indexes = [
            models.Index(fields=["submission"]),
            models.Index(fields=["student", "generated_at"]),
        ]

    def __str__(self):
        status = "correct" if self.is_correct else "incorrect"
        return f"Explanation: {self.student} | subpart {self.question_subpart_id} | {status}"


class GapSeverity(models.TextChoices):
    MILD = "mild", "Mild (score 40–50%)"
    MODERATE = "moderate", "Moderate (score 25–40%)"
    SEVERE = "severe", "Severe (score < 25%)"


class InsightType(models.TextChoices):
    STRUGGLING = "struggling", "Class Struggling (>40% below threshold)"
    AT_RISK = "at_risk", "At Risk (20–40% below threshold)"
    PROFICIENT = "proficient", "Class Proficient (<20% below threshold)"


class LearningGap(models.Model):
    """
    A detected weakness for a specific student in a specific chapter.

    Computed by scanning all Ticks for the student across questions in that
    chapter. Refreshed whenever new Ticks are acknowledged for the student.

    severity is derived from avg_score:
      severe:   avg_score < 0.25
      moderate: 0.25 <= avg_score < 0.40
      mild:     0.40 <= avg_score < 0.50
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="learning_gaps",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    chapter = models.ForeignKey(
        "core.Chapter",
        on_delete=models.CASCADE,
        related_name="learning_gaps",
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="learning_gaps",
        help_text="Context in which the gap was observed",
    )

    avg_score = models.FloatField(
        validators=FRACTION_VALIDATOR,
        help_text="Student average mark across all ticks in this chapter (0.0–1.0)",
    )
    severity = models.CharField(
        max_length=10,
        choices=GapSeverity.choices,
    )
    tick_count = models.PositiveIntegerField(
        help_text="Number of question-subpart ticks that contributed to this score",
    )

    is_resolved = models.BooleanField(
        default=False,
        help_text="Set True when avg_score rises >= 0.60 on a re-analysis",
    )
    detected_at = models.DateTimeField(auto_now_add=True)
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_learning_gaps"
        unique_together = [["student", "chapter", "subject_room"]]
        indexes = [
            models.Index(fields=["student", "is_resolved"]),
            models.Index(fields=["chapter", "is_resolved"]),
            models.Index(fields=["subject_room", "severity"]),
        ]

    def __str__(self):
        return f"Gap: {self.student} | {self.chapter} | " f"{self.severity} ({self.avg_score:.0%})"

    @staticmethod
    def severity_for_score(score: float) -> str:
        if score < 0.25:
            return GapSeverity.SEVERE
        if score < 0.40:
            return GapSeverity.MODERATE
        return GapSeverity.MILD


class ClassInsight(models.Model):
    """
    Aggregated performance insight for a teacher about their SubjectRoom on a Chapter.

    Generated by analysing all students' ticks in the subject_room for questions
    in the chapter. Refreshed after grading runs.

    insight_type:
      struggling: >40% of students below 50% average
      at_risk:    20–40% below threshold
      proficient: <20% below threshold
    """

    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="class_insights",
    )
    chapter = models.ForeignKey(
        "core.Chapter",
        on_delete=models.CASCADE,
        related_name="class_insights",
    )

    insight_type = models.CharField(max_length=15, choices=InsightType.choices)
    class_avg_score = models.FloatField(
        validators=FRACTION_VALIDATOR,
        help_text="Class average mark for this chapter (0.0–1.0)",
    )
    students_assessed = models.PositiveIntegerField(
        help_text="Number of students with at least 1 tick in this chapter",
    )
    students_struggling = models.PositiveIntegerField(
        help_text="Students with avg_score < 0.50 in this chapter",
    )
    pct_struggling = models.FloatField(
        validators=FRACTION_VALIDATOR,
        help_text="Fraction of assessed students who are struggling (0.0–1.0)",
    )

    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_class_insights"
        unique_together = [["subject_room", "chapter"]]
        indexes = [
            models.Index(fields=["subject_room", "insight_type"]),
        ]

    def __str__(self):
        return (
            f"Insight: {self.subject_room} | {self.chapter} | " f"{self.insight_type} (avg {self.class_avg_score:.0%})"
        )

    @staticmethod
    def insight_type_for_pct(pct: float) -> str:
        if pct > 0.40:
            return InsightType.STRUGGLING
        if pct > 0.20:
            return InsightType.AT_RISK
        return InsightType.PROFICIENT


class PerformancePrediction(models.Model):
    """
    Heuristic exam-readiness forecast for a student in a subject.

    Algorithm:
    1. Collect all StudentProficiency scores for the student across all tags
       in questions within the subject (filtered by subject_room.subject).
    2. Apply recency weighting: ticks from last 30 days count double.
    3. Weighted average = predicted_score.
    4. Confidence = sigmoid(tick_count / 20) — low when data is sparse.

    predicted_score  < 0.40 → needs_attention
    0.40 <= score < 0.65 → developing
    0.65 <= score < 0.80 → on_track
    score >= 0.80       → exam_ready
    """

    class ReadinessLevel(models.TextChoices):
        NEEDS_ATTENTION = "needs_attention", "Needs Attention"
        DEVELOPING = "developing", "Developing"
        ON_TRACK = "on_track", "On Track"
        EXAM_READY = "exam_ready", "Exam Ready"

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="performance_predictions",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="performance_predictions",
    )

    predicted_score = models.FloatField(
        validators=FRACTION_VALIDATOR,
        help_text="Predicted performance score (0.0–1.0)",
    )
    confidence = models.FloatField(
        validators=FRACTION_VALIDATOR,
        help_text="Confidence in the prediction — low when tick data is sparse",
    )
    readiness_level = models.CharField(
        max_length=20,
        choices=ReadinessLevel.choices,
    )
    tick_count = models.PositiveIntegerField(
        help_text="Total ticks used to compute this prediction",
    )
    factors = models.JSONField(
        default=dict,
        help_text=(
            "Top contributing factors: "
            '{"strong_chapters": [...], "weak_chapters": [...], '
            '"recent_trend": "improving|declining|stable"}'
        ),
    )

    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_performance_predictions"
        unique_together = [["student", "subject_room"]]
        indexes = [
            models.Index(fields=["student", "readiness_level"]),
            models.Index(fields=["subject_room", "readiness_level"]),
        ]

    def __str__(self):
        return (
            f"Prediction: {self.student} | {self.subject_room} | "
            f"{self.readiness_level} ({self.predicted_score:.0%}, "
            f"confidence {self.confidence:.0%})"
        )

    @staticmethod
    def readiness_for_score(score: float) -> str:
        if score >= 0.80:
            return PerformancePrediction.ReadinessLevel.EXAM_READY
        if score >= 0.65:
            return PerformancePrediction.ReadinessLevel.ON_TRACK
        if score >= 0.40:
            return PerformancePrediction.ReadinessLevel.DEVELOPING
        return PerformancePrediction.ReadinessLevel.NEEDS_ATTENTION


# ─────────────────────────────────────────────────────────────────────────────
# Content Recommendations
# ─────────────────────────────────────────────────────────────────────────────


class RecommendationReason(models.TextChoices):
    SEVERE_GAP = "severe_gap", "Severe Gap — urgent remediation needed"
    MODERATE_GAP = "moderate_gap", "Moderate Gap — needs more practice"
    MILD_GAP = "mild_gap", "Mild Gap — a few more attempts recommended"
    SPACED_REVIEW = "spaced_review", "Spaced Review — reinforce resolved gap"
    NEXT_TOPIC = "next_topic", "Next Topic — ready to progress"


class RecommendationPriority(models.IntegerChoices):
    URGENT = 1, "Urgent"
    HIGH = 2, "High"
    MEDIUM = 3, "Medium"
    LOW = 4, "Low"


class ContentRecommendation(models.Model):
    """
    A single "practice this next" recommendation for a student.

    Generated by scanning LearningGap and PerformancePrediction data.

    Priority rules (lower number = higher priority):
      1 (urgent)  — severe active gap
      2 (high)    — moderate active gap  OR  spaced_review of recently resolved gap
      3 (medium)  — mild active gap
      4 (low)     — next_topic progression (student ready to advance)

    is_actioned becomes True when the student opens or submits the problem set.
    Stale recommendations (superseded by re-analysis) are soft-deleted via is_active=False.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="content_recommendations",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="content_recommendations",
    )
    chapter = models.ForeignKey(
        "core.Chapter",
        on_delete=models.CASCADE,
        related_name="content_recommendations",
    )
    problem_set = models.ForeignKey(
        "core.ProblemSet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_recommendations",
        help_text="Specific problem set to attempt (null = any set in the chapter)",
    )

    reason = models.CharField(max_length=20, choices=RecommendationReason.choices)
    priority = models.PositiveSmallIntegerField(
        choices=RecommendationPriority.choices,
        help_text="Lower = more urgent",
    )

    # Snapshot of the score that triggered this recommendation (for audit / display)
    score_snapshot = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text="Student avg score in this chapter when the recommendation was generated",
    )

    is_actioned = models.BooleanField(
        default=False,
        help_text="True once the student has opened or submitted the recommended problem set",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="False when superseded by a newer analysis run",
    )

    generated_at = models.DateTimeField(auto_now_add=True)
    actioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_content_recommendations"
        # Only one active recommendation per student × chapter × subject_room
        unique_together = [["student", "chapter", "subject_room"]]
        indexes = [
            models.Index(fields=["student", "is_active", "priority"]),
            models.Index(fields=["subject_room", "is_active"]),
        ]

    def __str__(self):
        return f"Rec: {self.student} | {self.chapter} | " f"{self.get_reason_display()} (p{self.priority})"

    @staticmethod
    def priority_for_reason(reason: str) -> int:
        mapping = {
            RecommendationReason.SEVERE_GAP: RecommendationPriority.URGENT,
            RecommendationReason.MODERATE_GAP: RecommendationPriority.HIGH,
            RecommendationReason.SPACED_REVIEW: RecommendationPriority.HIGH,
            RecommendationReason.MILD_GAP: RecommendationPriority.MEDIUM,
            RecommendationReason.NEXT_TOPIC: RecommendationPriority.LOW,
        }
        return mapping.get(reason, RecommendationPriority.MEDIUM)  # type: ignore[call-overload]


class PracticePlan(models.Model):
    """
    A daily practice plan for a student in a SubjectRoom.

    Bundles the top N active ContentRecommendations into a digestible plan.
    One plan per student × subject_room × date.

    estimated_minutes = sum of estimated_minutes for linked problem sets
    (defaults to 10 min per recommendation if problem set has no estimate).
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="practice_plans",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="practice_plans",
    )
    recommendations = models.ManyToManyField(
        ContentRecommendation,
        related_name="practice_plans",
        blank=True,
    )
    plan_date = models.DateField(help_text="The day this plan is intended for")
    estimated_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Total estimated practice time in minutes",
    )
    is_completed = models.BooleanField(
        default=False,
        help_text="True when the student has actioned all recommendations in the plan",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_practice_plans"
        unique_together = [["student", "subject_room", "plan_date"]]
        indexes = [
            models.Index(fields=["student", "plan_date"]),
            models.Index(fields=["subject_room", "plan_date"]),
        ]

    def __str__(self):
        return f"Plan: {self.student} | {self.subject_room} | " f"{self.plan_date} (~{self.estimated_minutes}min)"


# ─────────────────────────────────────────────────────────────
# Adaptive Learning Engine Models
# ─────────────────────────────────────────────────────────────


class MasteryLevel(models.TextChoices):
    UNKNOWN = "unknown", "Unknown (not attempted)"
    NOVICE = "novice", "Novice (0–39%)"
    DEVELOPING = "developing", "Developing (40–59%)"
    PROFICIENT = "proficient", "Proficient (60–79%)"
    MASTERED = "mastered", "Mastered (80%+)"


class LearningPathStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    STALE = "stale", "Stale (regenerated)"


class StepStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    SKIPPED = "skipped", "Skipped"


class KnowledgeNode(models.Model):
    """
    Represents a chapter as a node in the prerequisite knowledge graph.

    Prerequisites define the directed edges: a student should ideally master
    all prerequisites before tackling this chapter. The adaptive engine uses
    this graph to order chapters in a LearningPath.

    One KnowledgeNode per (subject, chapter) pair — shared across all students.
    Teachers and admins can curate the prerequisite relationships through admin.

    Examples:
      - "Quadratic Equations" depends on "Linear Equations"
      - "Fractions" depends on "Division"
      - "Photosynthesis" depends on "Cell Structure"
    """

    subject = models.ForeignKey(
        "core.Subject",
        on_delete=models.CASCADE,
        related_name="knowledge_nodes",
    )
    chapter = models.ForeignKey(
        "core.Chapter",
        on_delete=models.CASCADE,
        related_name="knowledge_nodes",
    )
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="unlocks",
        help_text="Chapters that should be mastered before this one",
    )
    difficulty_weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(5.0)],
        help_text="Relative difficulty 0.1–5.0; affects spaced repetition interval scaling",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_knowledge_nodes"
        unique_together = [["subject", "chapter"]]
        indexes = [
            models.Index(fields=["subject", "is_active"]),
        ]

    def __str__(self):
        return f"KNode: {self.subject.name} — {self.chapter.name}"


class StudentMastery(models.Model):
    """
    Tracks a student's current mastery level for a specific KnowledgeNode.

    mastery_score is an exponentially weighted moving average (EWMA) of the
    student's scores across all attempts at questions in this chapter:

        new_score = alpha * latest_score + (1 - alpha) * old_score
        (alpha = 0.3, so recent performance matters more)

    mastery_level is derived from mastery_score:
        unknown:    no attempts yet
        novice:     0.00–0.39
        developing: 0.40–0.59
        proficient: 0.60–0.79
        mastered:   0.80–1.00

    Used by the adaptive engine to:
    - Skip chapters the student has mastered
    - Prioritise chapters where the student is novice/developing
    - Decide whether prerequisites are met before advancing
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="masteries",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    knowledge_node = models.ForeignKey(
        KnowledgeNode,
        on_delete=models.CASCADE,
        related_name="masteries",
    )
    mastery_score = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="EWMA of scores across all attempts (0.0–1.0)",
    )
    mastery_level = models.CharField(
        max_length=12,
        choices=MasteryLevel.choices,
        default=MasteryLevel.UNKNOWN,
    )
    attempt_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of practice attempts contributing to this score",
    )
    last_attempted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student last practiced this chapter",
    )
    first_attempted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student first attempted this chapter",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_student_mastery"
        unique_together = [["student", "knowledge_node"]]
        indexes = [
            models.Index(fields=["student", "mastery_level"]),
            models.Index(fields=["knowledge_node", "mastery_level"]),
        ]

    def __str__(self):
        return (
            f"Mastery: {self.student} | {self.knowledge_node.chapter.name} | "
            f"{self.mastery_level} ({self.mastery_score:.0%})"
        )

    @staticmethod
    def level_from_score(score: float) -> str:
        if score >= 0.80:
            return MasteryLevel.MASTERED
        if score >= 0.60:
            return MasteryLevel.PROFICIENT
        if score >= 0.40:
            return MasteryLevel.DEVELOPING
        return MasteryLevel.NOVICE


class LearningPath(models.Model):
    """
    A personalised, ordered sequence of KnowledgeNodes for a student.

    Generated by the adaptive engine by:
    1. Collecting all KnowledgeNodes for the student's enrolled subjects
    2. Filtering out already-mastered nodes (score >= 0.80)
    3. Topologically ordering remaining nodes respecting prerequisite edges
    4. Interleaving spaced-repetition review nodes (recently mastered chapters
       that are due for review)

    Only one ACTIVE path exists per (student, subject_room) at a time.
    When regenerated, the old path is marked STALE.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="learning_paths",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="learning_paths",
    )
    status = models.CharField(
        max_length=10,
        choices=LearningPathStatus.choices,
        default=LearningPathStatus.ACTIVE,
    )
    total_steps = models.PositiveIntegerField(default=0)
    completed_steps = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_learning_paths"
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["subject_room", "status"]),
        ]

    def __str__(self):
        return (
            f"Path: {self.student} | {self.subject_room} | "
            f"{self.status} ({self.completed_steps}/{self.total_steps})"
        )

    @property
    def progress_pct(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps


class LearningPathStep(models.Model):
    """
    A single step in a LearningPath — one chapter to study or review.

    Steps are ordered by `position` (1-indexed). The adaptive engine sets
    `is_review=True` for steps inserted by the spaced-repetition scheduler
    (chapters due for review rather than first-time learning).

    When a student completes the assigned problem_set for this step, the
    step status is updated to COMPLETED and StudentMastery is refreshed.
    """

    learning_path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    knowledge_node = models.ForeignKey(
        KnowledgeNode,
        on_delete=models.CASCADE,
        related_name="path_steps",
    )
    problem_set = models.ForeignKey(
        "core.ProblemSet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="path_steps",
        help_text="Suggested problem set for this step; null = student chooses freely",
    )
    position = models.PositiveIntegerField(
        help_text="1-indexed order in the learning path",
    )
    status = models.CharField(
        max_length=12,
        choices=StepStatus.choices,
        default=StepStatus.PENDING,
    )
    is_review = models.BooleanField(
        default=False,
        help_text="True when inserted by spaced-repetition scheduler for review",
    )
    score_when_completed = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text="Score the student achieved when they completed this step",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_learning_path_steps"
        unique_together = [["learning_path", "position"]]
        indexes = [
            models.Index(fields=["learning_path", "status"]),
            models.Index(fields=["knowledge_node", "status"]),
        ]

    def __str__(self):
        review_tag = " [review]" if self.is_review else ""
        return f"Step {self.position}{review_tag}: " f"{self.knowledge_node.chapter.name} [{self.status}]"


class SpacedRepetitionEntry(models.Model):
    """
    SM-2-inspired spaced repetition schedule for a student × KnowledgeNode.

    After each practice session the scheduler updates:
    - interval_days: days until next review (starts at 1, grows exponentially)
    - easiness_factor: governs how fast the interval grows (starts at 2.5)
    - repetitions: count of consecutive successful reviews
    - next_review_date: today + interval_days

    SM-2 update rules (simplified):
      If score >= 0.60 (successful recall):
        if repetitions == 0: interval = 1
        elif repetitions == 1: interval = 6
        else: interval = round(prev_interval * easiness_factor)
        easiness_factor = max(1.3, ef + 0.1 - (1-score)*0.8)
        repetitions += 1
      If score < 0.60 (failed recall):
        repetitions = 0
        interval = 1
        easiness_factor unchanged

    Entries with next_review_date <= today are surfaced by the adaptive engine
    as review steps in the student's LearningPath.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="srs_entries",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    knowledge_node = models.ForeignKey(
        KnowledgeNode,
        on_delete=models.CASCADE,
        related_name="srs_entries",
    )
    interval_days = models.PositiveIntegerField(
        default=1,
        help_text="Days until next review",
    )
    easiness_factor = models.FloatField(
        default=2.5,
        validators=[MinValueValidator(1.3), MaxValueValidator(5.0)],
        help_text="SM-2 easiness factor — controls interval growth rate",
    )
    repetitions = models.PositiveIntegerField(
        default=0,
        help_text="Consecutive successful review count",
    )
    next_review_date = models.DateField(
        help_text="Date on which this chapter is scheduled for review",
    )
    last_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_spaced_repetition_entries"
        unique_together = [["student", "knowledge_node"]]
        indexes = [
            models.Index(fields=["student", "next_review_date"]),
            models.Index(fields=["knowledge_node", "next_review_date"]),
        ]

    def __str__(self):
        return (
            f"SRS: {self.student} | {self.knowledge_node.chapter.name} | "
            f"next={self.next_review_date} interval={self.interval_days}d"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Weekly Class Summary Reports
# ─────────────────────────────────────────────────────────────────────────────


class WeeklyClassReport(models.Model):
    """
    An AI-generated, plain-language weekly summary of a SubjectRoom's activity.

    The teacher receives a narrative ("This week 18 of 24 students practised...
    the class is improving on Fractions but still struggling with Long Division")
    instead of having to read raw tables. The narrative is generated by the LLM
    cascade (Claude → Gemma → Ollama → stub) from a deterministic statistics
    snapshot computed from Tick data in the Mon–Sun window.

    The stats snapshot is stored alongside the narrative so the report renders
    fully even if the LLM provider is unavailable (the stub still produces a
    usable summary), and so the numbers behind the narrative are auditable.

    One report per (subject_room, week_start). Regenerating overwrites in place.
    """

    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="weekly_reports",
    )
    week_start = models.DateField(
        help_text="Monday of the reporting week (local date).",
    )
    week_end = models.DateField(
        help_text="Sunday of the reporting week (week_start + 6 days).",
    )

    summary_text = models.TextField(
        help_text="AI-generated plain-language narrative for the teacher.",
    )

    # ── Statistics snapshot (deterministic, computed from Ticks) ──────────────
    total_students = models.PositiveIntegerField(
        default=0,
        help_text="Students enrolled in the subject room.",
    )
    active_students = models.PositiveIntegerField(
        default=0,
        help_text="Students with at least one tick during the week.",
    )
    ticks_recorded = models.PositiveIntegerField(
        default=0,
        help_text="Total question-subpart ticks recorded during the week.",
    )
    class_avg_score = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="Mean tick mark across the week (0.0–1.0).",
    )
    struggling_chapters = models.JSONField(
        default=list,
        help_text='Weakest chapters this week: [{"chapter_id", "chapter_name", "avg_score", "tick_count"}].',
    )
    strong_chapters = models.JSONField(
        default=list,
        help_text='Strongest chapters this week: [{"chapter_id", "chapter_name", "avg_score", "tick_count"}].',
    )

    model_used = models.CharField(
        max_length=60,
        default="stub",
        help_text="LLM model ID that generated the narrative.",
    )
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_weekly_class_reports"
        unique_together = [["subject_room", "week_start"]]
        indexes = [
            models.Index(fields=["subject_room", "week_start"]),
        ]
        ordering = ["-week_start"]

    def __str__(self):
        return f"WeeklyReport: {self.subject_room} | week of {self.week_start} " f"(avg {self.class_avg_score:.0%})"

    @property
    def participation_rate(self) -> float:
        if self.total_students == 0:
            return 0.0
        return self.active_students / self.total_students


# ─────────────────────────────────────────────────────────────────────────────
# Intelligent Hint System
# ─────────────────────────────────────────────────────────────────────────────


class HintSequence(models.Model):
    """
    A cached, ordered set of progressive hints for a single QuestionSubpart.

    Hints guide a struggling student *toward* the answer without revealing it:
    level 1 is a gentle nudge ("recall what operation a 'sum' implies"), and each
    subsequent level is more concrete, with the final level stopping just short of
    stating the answer outright.

    The sequence is student-agnostic and generated once per subpart by the LLM
    cascade (Claude → Gemma → Ollama → stub), then reused for every student who
    asks for a hint. This keeps LLM cost to one call per question rather than one
    per student. Regenerating overwrites in place.

    The stub falls back to the subpart's static ``hint_text`` (if a teacher or
    Cabinet import supplied one) so the panel is always useful even with no LLM
    provider configured.
    """

    question_subpart = models.OneToOneField(
        "core.QuestionSubpart",
        on_delete=models.CASCADE,
        related_name="hint_sequence",
    )
    hints = models.JSONField(
        default=list,
        help_text='Ordered nudge→strong hints: [{"level": 1, "text": "..."}, ...].',
    )
    grade_level = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Grade level used to calibrate hint language.",
    )

    model_used = models.CharField(
        max_length=60,
        default="stub",
        help_text="LLM model ID that generated the hints.",
    )
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_hint_sequences"
        indexes = [
            models.Index(fields=["question_subpart"]),
        ]

    def __str__(self):
        return f"HintSequence: subpart {self.question_subpart_id} ({len(self.hints)} hints)"

    @property
    def hint_count(self) -> int:
        return len(self.hints) if isinstance(self.hints, list) else 0


class StudentMisconception(models.Model):
    """
    A structured diagnosis of *why* a student got a specific subpart wrong.

    Where SubpartExplanation produces free-text prose, this model captures a
    short, machine-friendly misconception label plus a remediation tip, so the
    same wrong-answer signal can power teacher dashboards and adaptive review
    (e.g. "8 students in this class share the 'distributes exponent over a sum'
    misconception").

    Generated asynchronously after a wrong answer (grading or SRS drill) by the
    LLM cascade. One per (student, subpart, submission) — regenerating updates
    in place. Only created for incorrect answers.
    """

    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="misconceptions",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    question_subpart = models.ForeignKey(
        "core.QuestionSubpart",
        on_delete=models.CASCADE,
        related_name="misconceptions",
    )
    submission = models.ForeignKey(
        "core.Submission",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="misconceptions",
        help_text="Null for SRS drill diagnoses not tied to a formal submission.",
    )

    student_answer = models.JSONField(
        help_text="The (incorrect) answer the student submitted.",
    )
    misconception_label = models.CharField(
        max_length=120,
        help_text="Short label for the underlying misconception (e.g. 'sign error on subtraction').",
    )
    diagnosis_text = models.TextField(
        help_text="Plain-language explanation of the faulty reasoning that led to the wrong answer.",
    )
    remediation_tip = models.TextField(
        blank=True,
        default="",
        help_text="Concrete, actionable suggestion for what the student should review or practise.",
    )
    grade_level = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )

    model_used = models.CharField(max_length=60, default="stub")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    detected_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_student_misconceptions"
        unique_together = [["student", "question_subpart", "submission"]]
        indexes = [
            models.Index(fields=["student", "detected_at"]),
            models.Index(fields=["question_subpart"]),
        ]

    def __str__(self):
        return f"Misconception: {self.student} | subpart {self.question_subpart_id} | {self.misconception_label}"


class ClassMisconceptionCluster(models.Model):
    """
    Class-level aggregation of StudentMisconception records for one SubjectRoom.

    Built by grouping recent StudentMisconception rows (across the room's students)
    by their normalised ``misconception_label`` and counting how many distinct
    students share each pattern. Surfaces "this misunderstanding is widespread
    in your class right now" to the teacher — the per-student data already lives
    in StudentMisconception; this cluster is a teacher-facing rollup.

    One row per (subject_room, normalised_label). Refreshing replaces the row
    in place — the table is a snapshot, not history.
    """

    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="misconception_clusters",
    )
    misconception_label = models.CharField(
        max_length=120,
        help_text="The shared, short misconception label (e.g. 'sign error on subtraction').",
    )
    student_count = models.PositiveIntegerField(
        default=0,
        help_text="Distinct students in the room exhibiting this misconception in the window.",
    )
    occurrence_count = models.PositiveIntegerField(
        default=0,
        help_text="Total StudentMisconception rows matched (one student may contribute several).",
    )
    sample_diagnosis = models.TextField(
        blank=True,
        default="",
        help_text="A representative diagnosis line copied from one of the underlying records.",
    )
    sample_remediation_tip = models.TextField(
        blank=True,
        default="",
        help_text="A representative remediation tip copied from one of the underlying records.",
    )
    window_start = models.DateTimeField(
        help_text="Start of the lookback window used to build this cluster.",
    )
    last_seen = models.DateTimeField(
        help_text="Most recent detected_at across the underlying StudentMisconception rows.",
    )
    refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_class_misconception_clusters"
        unique_together = [["subject_room", "misconception_label"]]
        indexes = [
            models.Index(fields=["subject_room", "-student_count"]),
        ]
        ordering = ["-student_count", "-last_seen"]

    def __str__(self):
        return f"ClassCluster: room {self.subject_room_id} | {self.misconception_label} ({self.student_count})"


# ─────────────────────────────────────────────────────────────────────────────
# Parent Intelligence Dashboard
# ─────────────────────────────────────────────────────────────────────────────


class ParentAlertSeverity(models.TextChoices):
    INFO = "info", "Info"
    ATTENTION = "attention", "Needs Attention"
    URGENT = "urgent", "Urgent"


class ParentProgressSummary(models.Model):
    """
    AI-generated, plain-language weekly progress summary for a parent about one child.

    Parents see *narratives*, not raw tables ("Aanya practised for 4 hours this week
    and improved 12% in Algebra, but still needs work on Geometry"). The narrative
    is generated by the LLM cascade from a deterministic stats snapshot computed
    from Tick + StudentProficiency data across all the child's SubjectRooms.

    Alongside the prose narrative we persist:
      • A structured stats snapshot, so the page renders even if the LLM provider
        is unavailable (the stub still produces a usable summary).
      • A list of suggested home activities — concrete things the parent can do
        WITH the child this week, calibrated to the weakest chapters.
      • A list of parent alerts — flags worth the parent's immediate attention
        (sharp performance drop, no practice in 7+ days, severe gap detected).

    One summary per (parent, child, week_start). Regenerating overwrites in place.
    """

    parent = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="parent_summaries",
        limit_choices_to={"role": "parent"},
    )
    child = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="parent_summaries_about",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    week_start = models.DateField(
        help_text="Monday of the reporting week (local date).",
    )
    week_end = models.DateField(
        help_text="Sunday of the reporting week (week_start + 6 days).",
    )

    summary_text = models.TextField(
        help_text="AI-generated plain-language weekly narrative for the parent.",
    )
    language = models.CharField(
        max_length=5,
        choices=ExplanationLanguage.choices,
        default=ExplanationLanguage.ENGLISH,
    )

    # ── Statistics snapshot (deterministic, computed from Ticks) ──────────────
    ticks_recorded = models.PositiveIntegerField(
        default=0,
        help_text="Total ticks the child recorded during the week.",
    )
    active_days = models.PositiveIntegerField(
        default=0,
        help_text="Distinct calendar days the child practised during the week.",
    )
    avg_score = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="Child's mean tick mark across the week (0.0–1.0).",
    )
    score_delta = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        help_text="Change in avg_score vs the prior week (positive = improving).",
    )
    weak_chapters = models.JSONField(
        default=list,
        help_text='Weakest chapters this week: [{"chapter_id", "chapter_name", "avg_score", "tick_count"}].',
    )
    strong_chapters = models.JSONField(
        default=list,
        help_text='Strongest chapters this week: [{"chapter_id", "chapter_name", "avg_score", "tick_count"}].',
    )

    home_activities = models.JSONField(
        default=list,
        help_text=(
            "Suggested at-home activities the parent can do with the child: "
            '[{"title", "description", "chapter_name"}].'
        ),
    )
    alerts = models.JSONField(
        default=list,
        help_text=("Parent alerts worth attention: " '[{"severity": "info|attention|urgent", "label", "detail"}].'),
    )

    model_used = models.CharField(
        max_length=60,
        default="stub",
        help_text="LLM model ID that generated the narrative.",
    )
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_parent_progress_summaries"
        unique_together = [["parent", "child", "week_start"]]
        indexes = [
            models.Index(fields=["parent", "week_start"]),
            models.Index(fields=["child", "week_start"]),
        ]
        ordering = ["-week_start"]

    def __str__(self):
        return f"ParentSummary: {self.parent} → {self.child} | week of {self.week_start}"

    @property
    def has_urgent_alert(self) -> bool:
        return any(isinstance(a, dict) and a.get("severity") == ParentAlertSeverity.URGENT for a in (self.alerts or []))


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Auto-Drafted Assignments
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentDraftStatus(models.TextChoices):
    PENDING = "pending", "Generating"
    READY = "ready", "Ready for review"
    APPROVED = "approved", "Approved"
    DISMISSED = "dismissed", "Dismissed"
    FAILED = "failed", "Failed"


class AssignmentDraft(models.Model):
    """
    An AI-assembled draft assignment for a SubjectRoom, awaiting teacher review.

    Creating an assignment by hand means a teacher must (1) know which chapters
    the class is weakest on, then (2) hunt the question bank for items at the right
    difficulty that haven't been over-used. This model does both automatically:

    A deterministic builder scans the room's recent Tick data, ranks chapters by
    class weakness, and selects questions from the bank that target those chapters
    around a requested difficulty — skipping questions already assigned to the room
    recently. The selection plus a plain-language rationale (generated by the LLM
    cascade Claude → Gemma → Ollama → stub) is stored as a *draft*: nothing is
    assigned to students until the teacher approves it.

    On approval the draft is materialised into a real ProblemSet + Assignment via
    the same models the manual flow uses, so downstream grading/analytics are
    unchanged. The structured `selected_questions` snapshot keeps the draft fully
    renderable even if the LLM provider is down, and makes the AI's choices
    auditable (each item records which class weakness it targets).
    """

    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="assignment_drafts",
    )
    requested_by = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="assignment_drafts_requested",
        limit_choices_to={"role": "teacher"},
    )

    status = models.CharField(
        max_length=10,
        choices=AssignmentDraftStatus.choices,
        default=AssignmentDraftStatus.PENDING,
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Suggested assignment title (teacher may edit on approval).",
    )
    rationale_text = models.TextField(
        blank=True,
        default="",
        help_text="AI-generated plain-language explanation of why these questions were chosen.",
    )

    # Requested parameters (echoed back so the UI can show what was asked for)
    target_difficulty = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Difficulty the teacher asked the draft to centre on (1=easiest, 5=hardest).",
    )
    requested_size = models.PositiveSmallIntegerField(
        default=8,
        help_text="Number of questions the teacher asked for.",
    )

    # ── Deterministic snapshot (computed from Tick data) ──────────────────────
    target_chapters = models.JSONField(
        default=list,
        help_text=(
            "Weak chapters the draft targets, weakest first: "
            '[{"chapter_id", "chapter_name", "avg_score", "tick_count"}].'
        ),
    )
    selected_questions = models.JSONField(
        default=list,
        help_text=(
            "Chosen questions in order: "
            '[{"question_id", "chapter_id", "chapter_name", "difficulty", '
            '"question_type", "preview", "reason"}].'
        ),
    )
    estimated_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Sum of estimated time across selected questions.",
    )

    # ── Materialisation links (set on approval) ───────────────────────────────
    approved_problem_set = models.ForeignKey(
        "core.ProblemSet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_draft",
        help_text="ProblemSet created when the teacher approved this draft.",
    )
    approved_assignment = models.ForeignKey(
        "core.Assignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_draft",
        help_text="Assignment created when the teacher approved this draft.",
    )

    model_used = models.CharField(
        max_length=60,
        default="stub",
        help_text="LLM model ID that generated the rationale.",
    )
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    error_detail = models.TextField(
        blank=True,
        default="",
        help_text="Populated when status=failed (e.g. no weak chapters / no questions in bank).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_assignment_drafts"
        indexes = [
            models.Index(fields=["subject_room", "status"]),
            models.Index(fields=["requested_by", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"AssignmentDraft #{self.pk} | {self.subject_room} | {self.status} ({self.question_count} Qs)"

    @property
    def question_count(self) -> int:
        return len(self.selected_questions or [])

    @property
    def is_actionable(self) -> bool:
        """True when the teacher can still approve or dismiss this draft."""
        return self.status == AssignmentDraftStatus.READY


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Open-Ended Response Grading
# ─────────────────────────────────────────────────────────────────────────────


class OpenResponseRubric(models.Model):
    """
    A grading rubric a teacher attaches to a short-answer (open-ended) subpart.

    Multiple-choice and numeric answers grade themselves by string/float
    comparison, but free-text answers do not — a student can be fully right while
    phrasing things completely differently from any stored key. This model gives
    the AI grader (and the teacher) the context it needs to score fairly:

    - ``model_answer`` is the ideal response the AI compares against.
    - ``criteria`` is an optional analytic breakdown — a list of marking points,
      each worth some marks — so the AI can award partial credit transparently
      and the teacher can see *why* a score was suggested.

    One rubric per subpart (the subpart's ``question_text`` supplies the prompt).
    Without a rubric the grader still works, falling back to ``model_answer`` only
    or, failing that, a keyword-overlap heuristic.
    """

    subpart = models.OneToOneField(
        "core.QuestionSubpart",
        on_delete=models.CASCADE,
        related_name="open_response_rubric",
        help_text="The short-answer subpart this rubric grades.",
    )
    max_marks = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Total marks an answer can earn.",
    )
    model_answer = models.TextField(
        blank=True,
        default="",
        help_text="The ideal/expected answer the AI grades responses against.",
    )
    criteria = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Optional analytic rubric points: "
            '[{"label": "...", "description": "...", "marks": 2}]. '
            "Marks should sum to max_marks; the grader awards per-point credit."
        ),
    )
    created_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="open_response_rubrics_created",
        limit_choices_to={"role": "teacher"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_open_response_rubrics"
        indexes = [
            models.Index(fields=["subpart"]),
        ]

    def __str__(self):
        return f"Rubric for subpart #{self.subpart_id} ({self.max_marks} marks)"


class OpenResponseGradeStatus(models.TextChoices):
    PENDING = "pending", "Awaiting AI grading"
    AI_GRADED = "ai_graded", "AI-graded, awaiting teacher review"
    REVIEWED = "reviewed", "Teacher-reviewed (final)"
    FAILED = "failed", "Grading failed"


class OpenResponseGrade(models.Model):
    """
    A single student's free-text answer plus its AI-suggested grade.

    The flow is **AI-assisted**, never fully automatic: the LLM cascade
    (Claude → Gemma → Ollama → heuristic stub) proposes a score, plain-language
    feedback, and an optional per-criterion breakdown; the teacher then reviews
    and can accept or override it. ``effective_score`` resolves to the teacher's
    ``final_score`` once reviewed, otherwise the AI's ``suggested_score`` — so the
    record is always usable while keeping the human firmly in the loop.

    The response is captured independently of the core grading pipeline (short
    answers auto-grade to 0 there), keeping this feature self-contained: a
    response can be entered by the teacher or fed in from any future submission
    integration. ``subject_room`` scopes ownership to the teacher who teaches it.
    """

    subpart = models.ForeignKey(
        "core.QuestionSubpart",
        on_delete=models.CASCADE,
        related_name="open_response_grades",
    )
    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="open_response_grades",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="open_response_grades",
        help_text="Room this response belongs to — scopes teacher ownership.",
    )
    assignment = models.ForeignKey(
        "core.Assignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="open_response_grades",
    )

    response_text = models.TextField(
        help_text="The student's free-text answer being graded.",
    )

    status = models.CharField(
        max_length=10,
        choices=OpenResponseGradeStatus.choices,
        default=OpenResponseGradeStatus.PENDING,
    )

    # ── AI-suggested grade ────────────────────────────────────────────────────
    max_marks = models.PositiveSmallIntegerField(
        default=5,
        help_text="Snapshot of the rubric's max marks at grading time.",
    )
    suggested_score = models.FloatField(
        null=True,
        blank=True,
        help_text="AI-suggested marks (0..max_marks). Null until graded.",
    )
    feedback = models.TextField(
        blank=True,
        default="",
        help_text="AI plain-language feedback for the student.",
    )
    criterion_scores = models.JSONField(
        default=list,
        blank=True,
        help_text='Per-criterion award: [{"label", "awarded", "max", "comment"}].',
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text="AI confidence in its suggested score (0..1).",
    )

    # ── Teacher review ────────────────────────────────────────────────────────
    final_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Teacher's final marks. Set on review; overrides suggested_score.",
    )
    teacher_comment = models.TextField(
        blank=True,
        default="",
        help_text="Optional teacher note added during review.",
    )
    reviewed_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="open_response_grades_reviewed",
        limit_choices_to={"role": "teacher"},
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    model_used = models.CharField(max_length=60, default="stub")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    error_detail = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_open_response_grades"
        indexes = [
            models.Index(fields=["subject_room", "status"]),
            models.Index(fields=["student", "-created_at"]),
            models.Index(fields=["subpart", "student"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"OpenResponseGrade #{self.pk} | {self.student} | subpart {self.subpart_id} | {self.status}"

    @property
    def effective_score(self) -> float | None:
        """The score that counts: teacher's final if reviewed, else the AI's."""
        if self.final_score is not None:
            return self.final_score
        return self.suggested_score

    @property
    def is_reviewed(self) -> bool:
        return self.status == OpenResponseGradeStatus.REVIEWED


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Intervention Suggestions
# ─────────────────────────────────────────────────────────────────────────────


class InterventionStatus(models.TextChoices):
    OPEN = "open", "Open (needs attention)"
    ACKNOWLEDGED = "acknowledged", "Acknowledged by teacher"
    DISMISSED = "dismissed", "Dismissed by teacher"
    RESOLVED = "resolved", "Resolved (student recovered)"


class InterventionSuggestion(models.Model):
    """
    An AI-generated, per-student intervention strategy for a teacher.

    Where ``LearningGap`` and ``StudentMisconception`` capture *what* a student
    is weak on, this model answers the teacher's next question — *"what do I do
    about it?"*. For each struggling student in a SubjectRoom it bundles the
    student's open learning gaps and most common misconceptions into a snapshot,
    then asks the LLM cascade (Claude → Gemma → Ollama → deterministic stub) to
    write a short, concrete intervention plan the teacher can act on this week.

    The snapshot (focus chapters, misconception labels, average score, gap count)
    is stored alongside the narrative so the card renders fully even when no LLM
    provider is configured (the stub composes a usable plan from the snapshot)
    and so the reasoning behind the plan stays auditable.

    ``priority`` (1–5, higher = more urgent) is derived deterministically from the
    severity and breadth of the gaps so the teacher's list sorts worst-first.

    One row per (subject_room, student); regenerating overwrites in place. A
    teacher can acknowledge, dismiss, or mark a suggestion resolved; a refresh
    that finds the student has recovered auto-resolves an open suggestion.
    """

    subject_room = models.ForeignKey(
        "core.SubjectRoom",
        on_delete=models.CASCADE,
        related_name="intervention_suggestions",
    )
    student = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="intervention_suggestions",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )

    status = models.CharField(
        max_length=12,
        choices=InterventionStatus.choices,
        default=InterventionStatus.OPEN,
    )
    priority = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1–5, higher = more urgent. Derived from gap severity and breadth.",
    )
    severity = models.CharField(
        max_length=10,
        choices=GapSeverity.choices,
        help_text="Worst gap severity contributing to this suggestion.",
    )

    strategy_text = models.TextField(
        help_text="AI-generated plain-language intervention plan for the teacher.",
    )

    # ── Snapshot of the evidence behind the suggestion ────────────────────────
    avg_score = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="Mean of the student's open-gap chapter scores (0.0–1.0).",
    )
    gap_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of open learning gaps this student has in the room.",
    )
    focus_chapters = models.JSONField(
        default=list,
        help_text='Weakest chapters: [{"chapter_id", "chapter_name", "avg_score", "severity"}].',
    )
    misconception_labels = models.JSONField(
        default=list,
        help_text='Most common misconceptions: [{"label", "count"}].',
    )

    acknowledged_by = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interventions_acknowledged",
        limit_choices_to={"role": "teacher"},
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    model_used = models.CharField(max_length=60, default="stub")
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_intervention_suggestions"
        unique_together = [["subject_room", "student"]]
        indexes = [
            models.Index(fields=["subject_room", "status", "-priority"]),
            models.Index(fields=["student", "status"]),
        ]
        ordering = ["-priority", "avg_score"]

    def __str__(self):
        return f"Intervention: {self.student} | {self.subject_room} | P{self.priority} ({self.status})"

    @staticmethod
    def priority_for(severity: str, gap_count: int) -> int:
        """
        Map severity + breadth to a 1–5 urgency score.

        A severe gap starts at 4, moderate at 3, mild at 2; each additional gap
        beyond the first nudges it up, capped at 5.
        """
        base = {GapSeverity.SEVERE: 4, GapSeverity.MODERATE: 3}.get(severity, 2)
        return max(1, min(5, base + max(0, gap_count - 1)))
