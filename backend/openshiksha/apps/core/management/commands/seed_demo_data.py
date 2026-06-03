"""
Management command: seed_demo_data

Creates a full demo school with real LaTeX question content.
Idempotent — safe to run multiple times.

Questions are namespaced with the ``seed-demo`` QuestionTag so they can be
found and replaced on each run without colliding with cabinet-imported questions
that share the same (standard, subject, chapter, type, difficulty) tuple.

Usage:
    python manage.py seed_demo_data
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
    Subject,
    SubjectRoom,
    User,
    UserRole,
)

DEMO_PASSWORD = "demo1234"


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

        student, created = User.objects.get_or_create(
            username="student_demo",
            defaults={
                "email": "student@demo.openshiksha.org",
                "first_name": "Arjun",
                "last_name": "Verma",
                "role": UserRole.STUDENT,
                "school": school,
                "grade": 10,
                "password": make_password(DEMO_PASSWORD),
            },
        )
        self._log(created, "Student", "student@demo.openshiksha.org")

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
        if created:
            subject_room.students.add(student)
            self.stdout.write("  [+] SubjectRoom: Mathematics \u2014 Class 10A")
        else:
            subject_room.students.add(student)
            self.stdout.write("  [=] SubjectRoom: Mathematics \u2014 Class 10A (existing)")

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
        questions_data = [
            {
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
        ]

        created_questions = []
        for qdata in questions_data:
            # Always create fresh — stale seed-demo questions were deleted above.
            question = Question.objects.create(
                school=None,
                standard=standard,
                subject=subject,
                chapter=chapter,
                question_type=qdata["question_type"],
                difficulty=qdata["difficulty"],
                is_active=True,
            )
            question.tags.add(tag_algebra, tag_quadratic, tag_seed_demo)

            QuestionSubpart.objects.create(
                question=question,
                index=0,
                subpart_type=qdata["question_type"],
                question_text=qdata["question_text"],
                options=qdata["options"],
                correct_answer=qdata["correct_answer"],
                variable_constraints=qdata.get("variable_constraints"),
            )
            created_questions.append(question)

        self.stdout.write(f"  [+] {len(created_questions)} demo questions created")

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

        # ── Summary ────────────────────────────────────────────────────────────
        self.stdout.write("\nDemo ready! Log in at http://localhost:5173")
        self.stdout.write(f"  student_demo       / {DEMO_PASSWORD}  (student)")
        self.stdout.write(f"  teacher_demo       / {DEMO_PASSWORD}  (teacher)")
        self.stdout.write(f"  parent_demo        / {DEMO_PASSWORD}  (parent — linked to student_demo)")
        self.stdout.write(f"  admin_demo         / {DEMO_PASSWORD}  (school admin)")
        self.stdout.write(f"  openstudent_demo   / {DEMO_PASSWORD}  (open student)")
        self.stdout.write("")

    def _log(self, created: bool, label: str, name: str) -> None:
        prefix = "[+]" if created else "[=]"
        action = "Created" if created else "Exists"
        self.stdout.write(f"  {prefix} {label}: {name} ({action})")
