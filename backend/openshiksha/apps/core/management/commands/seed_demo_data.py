"""
Management command: seed_demo_data

Creates a full demo school with real LaTeX question content.
Idempotent — safe to run multiple times (uses get_or_create throughout).

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
            },
        ]

        created_questions = []
        for i, qdata in enumerate(questions_data):
            question, q_created = Question.objects.get_or_create(
                school=None,
                standard=standard,
                subject=subject,
                chapter=chapter,
                question_type=qdata["question_type"],
                difficulty=qdata["difficulty"],
                defaults={"is_active": True},
            )
            if q_created:
                question.tags.add(tag_algebra, tag_quadratic)

            subpart, _ = QuestionSubpart.objects.get_or_create(
                question=question,
                index=0,
                defaults={
                    "question_text": qdata["question_text"],
                    "options": qdata["options"],
                    "correct_answer": qdata["correct_answer"],
                },
            )
            # Update text/options even if subpart already existed (allows re-seeding content)
            if not _:
                subpart.question_text = qdata["question_text"]
                subpart.options = qdata["options"]
                subpart.correct_answer = qdata["correct_answer"]
                subpart.save(update_fields=["question_text", "options", "correct_answer"])

            created_questions.append(question)

        self.stdout.write(f"  [+] {len(created_questions)} questions with LaTeX content")

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
        self.stdout.write(f"  Student:  student@demo.openshiksha.org / {DEMO_PASSWORD}")
        self.stdout.write(f"  Teacher:  teacher@demo.openshiksha.org / {DEMO_PASSWORD}")
        self.stdout.write("")

    def _log(self, created: bool, label: str, name: str) -> None:
        prefix = "[+]" if created else "[=]"
        action = "Created" if created else "Exists"
        self.stdout.write(f"  {prefix} {label}: {name} ({action})")
