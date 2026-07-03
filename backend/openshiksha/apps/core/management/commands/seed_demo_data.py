"""
Management command: seed_demo_data

Creates a full demo school with real LaTeX question content.
Idempotent — safe to run multiple times.

Questions are namespaced with the ``seed-demo`` QuestionTag so they can be
found and replaced on each run without colliding with cabinet-imported questions
that share the same (standard, subject, chapter, type, difficulty) tuple.

Usage:
    python manage.py seed_demo_data

─────────────────────────────────────────────────────────────────────────────
Launch T-1 audit (2026-07-01) — seed vs. the shot list in
``docs/launch/video-plan.md``. Every AI-driven dashboard the video films
(parent weekly summary, streak sparklines, class insights, performance
predictions) reads from ``edge.Tick`` rows, not ``Submission`` rows. The
original seed created zero ticks and a single student, so those surfaces would
have filmed empty. This command now also seeds:

  * A cohort of five named Class-10A students (shots 2 & 3 need two+ students
    with real names for the split-screen "different numbers" beat).
  * A second chapter (Linear Equations) so parent/teacher dashboards can show a
    genuine strong-vs-weak split rather than one lonely chapter.
  * ~2 weeks of back-dated Tick history per student with per-student ability
    profiles, so streaks, sparklines, class insights, gap detection and the
    parent weekly summary are all non-empty and believable on camera.
  * Graded Submissions for the standing assignment so the teacher's assignment
    view and the student's history are populated.
  * Per-student StudentStreak rows (hero student on a 14-day streak).

Known remaining gaps (out of scope for this pass — larger than a seed tweak):
  * Derived AI artefacts (LearningGap / PerformancePrediction / ParentProgress
    Summary rows) are produced by Celery analytics tasks, not seeded directly —
    the recording environment must run those tasks (or the on-demand refresh
    endpoints) once after seeding so shot 9's summary card is materialised.
  * Shot 6 still needs a live ANTHROPIC key so the explanation badge reads
    ``✨ AI-generated`` rather than ``Auto-built``.
"""

from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    Question,
    QuestionSubpart,
    QuestionTag,
    QuestionType,
    School,
    Standard,
    StudentStreak,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)

DEMO_PASSWORD = "demo1234"

# Class-10A demo cohort. ``ability`` (0.0–1.0) drives the back-dated Tick
# history so dashboards show a believable spread — a couple of stars, a couple
# in the middle, one student who needs help. ``streak`` seeds StudentStreak so
# streak sparklines are non-empty. Arjun is the "hero" student the parent
# (Meena Verma) is linked to and the one most shots follow.
DEMO_STUDENTS = [
    {"username": "student_demo", "first": "Arjun", "last": "Verma", "ability": 0.72, "streak": 14},
    {"username": "student_ananya", "first": "Ananya", "last": "Iyer", "ability": 0.88, "streak": 9},
    {"username": "student_rohan", "first": "Rohan", "last": "Gupta", "ability": 0.61, "streak": 5},
    {"username": "student_fatima", "first": "Fatima", "last": "Sheikh", "ability": 0.38, "streak": 2},
    {"username": "student_kabir", "first": "Kabir", "last": "Nair", "ability": 0.55, "streak": 7},
]

# Days (offsets back from "now") on which every student was active. Two small
# gaps keep it from looking synthetic while staying inside the current + prior
# week windows the parent/teacher summaries compare.
ACTIVITY_DAY_OFFSETS = [0, 1, 2, 4, 5, 6, 8, 9, 11, 12, 13]


class Command(BaseCommand):
    help = "Seed the database with demo data for development and testing"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...\n")

        # ── Educational structure ──────────────────────────────────────────────
        board, created = Board.objects.get_or_create(
            name="CBSE",
            defaults={"description": "Central Board of Secondary Education"},
        )
        self._log(created, "Board", "CBSE")

        standard, created = Standard.objects.get_or_create(
            number=10,
            defaults={"description": "Class 10"},
        )
        self._log(created, "Standard", "Class 10")

        subject, created = Subject.objects.get_or_create(
            name="Mathematics",
            defaults={"description": "Mathematics for CBSE"},
        )
        self._log(created, "Subject", "Mathematics")

        chapter, created = Chapter.objects.get_or_create(
            name="Quadratic Equations",
            subject=subject,
            standard=standard,
            defaults={"order": 4, "description": "Solving quadratic equations"},
        )
        self._log(created, "Chapter", "Quadratic Equations")

        # A second chapter so parent/teacher dashboards can show a real
        # strong-vs-weak split (the demo cohort does better on linear equations
        # than on quadratics — see the per-chapter offsets in the tick loop).
        chapter2, created = Chapter.objects.get_or_create(
            name="Linear Equations in Two Variables",
            subject=subject,
            standard=standard,
            defaults={"order": 3, "description": "Solving pairs of linear equations"},
        )
        self._log(created, "Chapter", "Linear Equations in Two Variables")

        # ── School and classroom ───────────────────────────────────────────────
        school, created = School.objects.get_or_create(
            name="OpenShiksha Demo School",
            defaults={"board": board, "city": "Bengaluru", "state": "Karnataka"},
        )
        self._log(created, "School", "OpenShiksha Demo School")

        classroom, created = ClassRoom.objects.get_or_create(
            school=school,
            standard=standard,
            division="A",
            academic_year="2025-26",
        )
        self._log(created, "ClassRoom", "Class 10A")

        # ── Users ──────────────────────────────────────────────────────────────
        teacher, created = User.objects.get_or_create(
            username="teacher_demo",
            defaults={
                "email": "teacher@demo.openshiksha.org",
                "first_name": "Priya",
                "last_name": "Sharma",
                "role": UserRole.TEACHER,
                "school": school,
                "password": make_password(DEMO_PASSWORD),
            },
        )
        self._log(created, "Teacher", "teacher@demo.openshiksha.org")

        # Class-10A cohort. ``student`` (Arjun) stays the hero the parent links
        # to and most shots follow; ``students`` is the whole roster used for
        # SubjectRoom enrolment and the seeded activity history.
        students = []
        for spec in DEMO_STUDENTS:
            student_user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": f"{spec['username']}@demo.openshiksha.org",
                    "first_name": spec["first"],
                    "last_name": spec["last"],
                    "role": UserRole.STUDENT,
                    "school": school,
                    "grade": 10,
                    "password": make_password(DEMO_PASSWORD),
                },
            )
            students.append(student_user)
            self._log(created, "Student", f"{spec['first']} {spec['last']}")
        student = students[0]

        parent, created = User.objects.get_or_create(
            username="parent_demo",
            defaults={
                "email": "parent@demo.openshiksha.org",
                "first_name": "Meena",
                "last_name": "Verma",
                "role": UserRole.PARENT,
                "school": school,
                "password": make_password(DEMO_PASSWORD),
            },
        )
        if created or not parent.children.filter(pk=student.pk).exists():
            parent.children.add(student)
        self._log(created, "Parent", "parent@demo.openshiksha.org")

        _admin, created = User.objects.get_or_create(
            username="admin_demo",
            defaults={
                "email": "admin@demo.openshiksha.org",
                "first_name": "Rakesh",
                "last_name": "Iyer",
                "role": UserRole.ADMIN,
                "school": school,
                "is_staff": True,
                "password": make_password(DEMO_PASSWORD),
            },
        )
        self._log(created, "Admin", "admin@demo.openshiksha.org")

        _open_student, created = User.objects.get_or_create(
            username="openstudent_demo",
            defaults={
                "email": "open@demo.openshiksha.org",
                "first_name": "Sara",
                "last_name": "Khan",
                "role": UserRole.OPEN_STUDENT,
                "grade": 9,
                "password": make_password(DEMO_PASSWORD),
            },
        )
        self._log(created, "OpenStudent", "open@demo.openshiksha.org")

        # ── SubjectRoom ────────────────────────────────────────────────────────
        subject_room, created = SubjectRoom.objects.get_or_create(
            classroom=classroom,
            subject=subject,
            defaults={"teacher": teacher},
        )
        subject_room.students.add(*students)
        if created:
            self.stdout.write(f"  [+] SubjectRoom: Mathematics \u2014 Class 10A ({len(students)} students)")
        else:
            self.stdout.write(f"  [=] SubjectRoom: Mathematics \u2014 Class 10A ({len(students)} students, existing)")

        # ── Question tags ──────────────────────────────────────────────────────
        tag_algebra, _ = QuestionTag.objects.get_or_create(name="algebra", defaults={"tag_type": "concept"})
        tag_quadratic, _ = QuestionTag.objects.get_or_create(
            name="quadratic-equations", defaults={"tag_type": "concept"}
        )
        # ``seed-demo`` is the idempotency namespace: we delete any previously
        # seeded questions (tagged seed-demo) and recreate them fresh.  This
        # avoids the MultipleObjectsReturned error that occurs when
        # get_or_create uses only (school, standard, subject, chapter,
        # question_type, difficulty) — a lookup that matches cabinet-imported
        # questions sharing those same attributes.
        tag_seed_demo, _ = QuestionTag.objects.get_or_create(name="seed-demo", defaults={"tag_type": "source"})
        stale_qs = Question.objects.filter(tags=tag_seed_demo)
        stale_count = stale_qs.count()
        stale_qs.delete()
        if stale_count:
            self.stdout.write(f"  [~] Removed {stale_count} stale demo question(s) for re-seed")

        # ── Questions with LaTeX content ───────────────────────────────────────
        # ``chapter`` defaults to the quadratics chapter; the linear-equations
        # entries carry an explicit chapter so the seeded history spans two topics.
        questions_data = [
            {
                "chapter": chapter,
                "question_type": QuestionType.MCQ,
                "difficulty": 2,
                "question_text": ("Solve $x^2 - 5x + 6 = 0$. " "Which values of $x$ satisfy this equation?"),
                "options": [
                    {"key": "A", "text": "$x = 2$ and $x = 3$"},
                    {"key": "B", "text": "$x = 1$ and $x = 6$"},
                    {"key": "C", "text": "$x = -2$ and $x = -3$"},
                    {"key": "D", "text": "$x = 3$ and $x = 4$"},
                ],
                "correct_answer": {"type": "mcq", "answer": "A"},
            },
            {
                "chapter": chapter,
                "question_type": QuestionType.MCQ,
                "difficulty": 2,
                "question_text": (
                    "The discriminant of $ax^2 + bx + c = 0$ is given by $\\Delta = b^2 - 4ac$. "
                    "If $\\Delta > 0$, the equation has:"
                ),
                "options": [
                    {"key": "A", "text": "No real roots"},
                    {"key": "B", "text": "Exactly one real root"},
                    {"key": "C", "text": "Two distinct real roots"},
                    {"key": "D", "text": "Two equal real roots"},
                ],
                "correct_answer": {"type": "mcq", "answer": "C"},
            },
            {
                "chapter": chapter,
                "question_type": QuestionType.NUMERIC,
                "difficulty": 3,
                "question_text": (
                    "What is the sum of the roots of $2x^2 - 7x + 3 = 0$? " "(Hint: sum of roots $= -b/a$)"
                ),
                "options": None,
                "correct_answer": {"type": "numeric", "answer": 3.5},
                "variable_constraints": None,
            },
            {
                "chapter": chapter,
                "question_type": QuestionType.NUMERIC,
                "difficulty": 2,
                "question_text": r"Solve: ${{a}}x + {{b}} = {{c}}$. Find $x$.",
                "options": None,
                "correct_answer": {"type": "numeric", "answer": "({{c}} - {{b}}) / {{a}}"},
                "variable_constraints": {
                    "a": {"min": 2, "max": 9, "integer": True},
                    "b": {"min": 1, "max": 20, "integer": True},
                    "c": {"min": 10, "max": 50, "integer": True},
                },
            },
            {
                "chapter": chapter2,
                "question_type": QuestionType.MCQ,
                "difficulty": 2,
                "question_text": (
                    "The pair $2x + 3y = 12$ and $x - y = 1$ intersects at exactly one point. "
                    "This means the system is:"
                ),
                "options": [
                    {"key": "A", "text": "Inconsistent (no solution)"},
                    {"key": "B", "text": "Consistent with a unique solution"},
                    {"key": "C", "text": "Consistent with infinitely many solutions"},
                    {"key": "D", "text": "Undefined"},
                ],
                "correct_answer": {"type": "mcq", "answer": "B"},
            },
            {
                "chapter": chapter2,
                "question_type": QuestionType.NUMERIC,
                "difficulty": 2,
                "question_text": ("Solve $x + y = 10$ and $x - y = 4$. " "What is the value of $x$?"),
                "options": None,
                "correct_answer": {"type": "numeric", "answer": 7},
                "variable_constraints": None,
            },
        ]

        created_questions = []
        subparts_by_chapter = {chapter.id: [], chapter2.id: []}
        for qdata in questions_data:
            # Always create fresh — stale seed-demo questions were deleted above.
            q_chapter = qdata["chapter"]
            question = Question.objects.create(
                school=None,
                standard=standard,
                subject=subject,
                chapter=q_chapter,
                question_type=qdata["question_type"],
                difficulty=qdata["difficulty"],
                is_active=True,
            )
            question.tags.add(tag_algebra, tag_seed_demo)
            if q_chapter.id == chapter.id:
                question.tags.add(tag_quadratic)

            subpart = QuestionSubpart.objects.create(
                question=question,
                index=0,
                subpart_type=qdata["question_type"],
                question_text=qdata["question_text"],
                options=qdata["options"],
                correct_answer=qdata["correct_answer"],
                variable_constraints=qdata.get("variable_constraints"),
            )
            subparts_by_chapter[q_chapter.id].append(subpart)
            if q_chapter.id == chapter.id:
                created_questions.append(question)

        self.stdout.write(f"  [+] {len(questions_data)} demo questions created across 2 chapters")

        # ── ProblemSet ─────────────────────────────────────────────────────────
        problem_set, created = ProblemSet.objects.get_or_create(
            school=None,
            standard=standard,
            subject=subject,
            chapter=chapter,
            number=1,
            defaults={
                "title": "Quadratic Equations \u2013 Practice Set 1",
                "description": "Foundational practice on solving quadratic equations.",
                "estimated_minutes": 20,
                "is_active": True,
            },
        )
        problem_set.questions.set(created_questions)
        self._log(created, "ProblemSet", problem_set.title)

        # ── Assignment ─────────────────────────────────────────────────────────
        assignment, created = Assignment.objects.get_or_create(
            subject_room=subject_room,
            problem_set=problem_set,
            number=1,
            defaults={
                "assigned_by": teacher,
                "due_at": timezone.now() + timedelta(days=7),
            },
        )
        self._log(created, "Assignment", f"#{assignment.pk} (due in 7 days)")

        # ── Activity history (ticks, streaks, submissions) ─────────────────────
        self._seed_activity_history(students, subject_room, subparts_by_chapter, chapter, chapter2, assignment)

        # ── Summary ────────────────────────────────────────────────────────────
        self.stdout.write("\nDemo ready! Log in at http://localhost:5173")
        self.stdout.write(f"  student_demo       / {DEMO_PASSWORD}  (student — Arjun, hero, 14-day streak)")
        for spec in DEMO_STUDENTS[1:]:
            self.stdout.write(f"  {spec['username']:<18} / {DEMO_PASSWORD}  (student — {spec['first']} {spec['last']})")
        self.stdout.write(f"  teacher_demo       / {DEMO_PASSWORD}  (teacher)")
        self.stdout.write(f"  parent_demo        / {DEMO_PASSWORD}  (parent — linked to student_demo)")
        self.stdout.write(f"  admin_demo         / {DEMO_PASSWORD}  (school admin)")
        self.stdout.write(f"  openstudent_demo   / {DEMO_PASSWORD}  (open student)")
        self.stdout.write("")
        self.stdout.write(
            "Note: AI dashboards (parent summary, class insights, predictions) are\n"
            "materialised by the analytics Celery tasks / refresh endpoints — run\n"
            "those once against this seeded data before recording shot 9."
        )
        self.stdout.write("")

    def _seed_activity_history(
        self, students, subject_room, subparts_by_chapter, quad_chapter, linear_chapter, assignment
    ):
        """Back-date a couple of weeks of Tick activity so every AI dashboard the
        launch video films is non-empty and believable. Idempotent."""
        from openshiksha.apps.edge.models import Tick

        now = timezone.now()

        # Idempotency: clear prior seeded activity so re-runs don't stack. (Ticks
        # on recreated seed-demo subparts were already cascade-removed above.)
        Tick.objects.filter(student__in=students, subject_room=subject_room).delete()
        Submission.objects.filter(student__in=students, assignment=assignment).delete()

        # The cohort finds linear equations easier than quadratics — a clean
        # strong-vs-weak split for the parent/teacher dashboards.
        chapter_offset = {quad_chapter.id: -0.12, linear_chapter.id: 0.12}

        tick_count = 0
        for s_idx, (spec, student_user) in enumerate(zip(DEMO_STUDENTS, students)):
            ability = spec["ability"]
            for day_offset in ACTIVITY_DAY_OFFSETS:
                activity_dt = now - timedelta(days=day_offset)
                # Gentle upward trend in the current week so predictions and the
                # parent summary read "improving" rather than flat.
                recency_bonus = 0.08 if day_offset < 7 else 0.0
                for chapter_id, subparts in subparts_by_chapter.items():
                    prob = max(0.0, min(1.0, ability + chapter_offset[chapter_id] + recency_bonus))
                    for subpart in subparts:
                        # Deterministic pseudo-random binary mark — reproducible
                        # across re-seeds, no RNG state to manage.
                        bucket = (day_offset * 7 + subpart.pk * 13 + s_idx * 29 + chapter_id * 3) % 100
                        mark = 1.0 if bucket < prob * 100 else 0.0
                        tick = Tick.objects.create(
                            student=student_user,
                            question_subpart=subpart,
                            submission=None,
                            subject_room=subject_room,
                            mark=mark,
                        )
                        # auto_now_add blocks created_at on create — back-date via update.
                        Tick.objects.filter(pk=tick.pk).update(created_at=activity_dt)
                        tick_count += 1

            # A graded submission for the standing assignment so the teacher's
            # assignment view and the student's history are populated. Score is
            # set up front so the post-save grading signal short-circuits (the
            # "already graded" guard) — no Celery worker required to seed.
            Submission.objects.create(
                assignment=assignment,
                student=student_user,
                score=round(max(0.05, min(1.0, ability)), 2),
                completion=1.0,
                answers={},
                submitted_at=now - timedelta(hours=6 + s_idx),
            )

            # Streak row so sparklines are non-empty; last activity is today so
            # the run reads as live. Written *after* the submission above, whose
            # post-save signal also touches the streak — this explicit value wins.
            StudentStreak.objects.update_or_create(
                student=student_user,
                defaults={
                    "current_streak": spec["streak"],
                    "longest_streak": spec["streak"],
                    "last_activity_date": now.date(),
                    "streak_grace_used": False,
                },
            )

        self.stdout.write(
            f"  [+] Seeded {tick_count} ticks + {len(students)} streaks + "
            f"{len(students)} submissions across ~{len(ACTIVITY_DAY_OFFSETS)} active days"
        )

    def _log(self, created: bool, label: str, name: str) -> None:
        prefix = "[+]" if created else "[=]"
        action = "Created" if created else "Exists"
        self.stdout.write(f"  {prefix} {label}: {name} ({action})")
