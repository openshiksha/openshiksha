"""
Tests for the periodic due-date reminder task (P5).
"""

from datetime import timedelta

import pytest

from django.core import mail
from django.utils import timezone

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="Reminder School", board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.create(name="Science")


@pytest.fixture
def chapter(db, subject, standard):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.create(name="Motion", subject=subject, standard=standard)


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="reminder_teacher", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(
        username="reminder_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        email="student@test.example",
    )


@pytest.fixture(autouse=True)
def use_locmem_email(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []


def _make_assignment(school, standard, subject, chapter, teacher, students, due_in_hours, target=None):
    from openshiksha.apps.core.models import Assignment, ClassRoom, ProblemSet, SubjectRoom

    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A")
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    for s in students:
        subject_room.students.add(s)

    problem_set = ProblemSet.objects.create(
        title="Forces Quiz",
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        number=1,
        created_by=teacher,
    )

    return Assignment.objects.create(
        problem_set=problem_set,
        subject_room=subject_room,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(hours=due_in_hours),
        target_student=target,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDueDateReminders:
    def test_reminder_sent_for_upcoming_assignment(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.models import AssignmentReminder
        from openshiksha.apps.core.tasks import send_due_date_reminders

        _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=12)
        stats = send_due_date_reminders()

        assert stats["reminded"] == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["student@test.example"]
        assert "due" in mail.outbox[0].subject.lower()
        assert AssignmentReminder.objects.filter(student=student).count() == 1

    def test_no_duplicate_reminder_on_rerun(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.tasks import send_due_date_reminders

        _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=12)
        send_due_date_reminders()
        mail.outbox = []
        stats = send_due_date_reminders()

        assert stats["reminded"] == 0
        assert len(mail.outbox) == 0

    def test_opted_out_student_not_reminded(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.tasks import send_due_date_reminders

        student.email_reminders_opt_out = True
        student.save(update_fields=["email_reminders_opt_out"])
        _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=12)

        stats = send_due_date_reminders()
        assert stats["reminded"] == 0
        assert len(mail.outbox) == 0

    def test_submitted_student_not_reminded(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.models import Submission
        from openshiksha.apps.core.tasks import send_due_date_reminders

        assignment = _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=12)
        Submission.objects.create(assignment=assignment, student=student, submitted_at=timezone.now())
        # Submitting can fire grading emails via signals; ignore those and assert
        # that no *reminder* email was sent.
        mail.outbox = []

        stats = send_due_date_reminders()
        assert stats["reminded"] == 0
        reminder_emails = [m for m in mail.outbox if "due" in m.subject.lower()]
        assert len(reminder_emails) == 0

    def test_assignment_outside_window_not_reminded(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.tasks import send_due_date_reminders

        # Due in 48h, default window is 24h.
        _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=48)

        stats = send_due_date_reminders()
        assert stats["assignments"] == 0
        assert len(mail.outbox) == 0

    def test_past_due_assignment_not_reminded(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.tasks import send_due_date_reminders

        _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=-2)

        stats = send_due_date_reminders()
        assert stats["assignments"] == 0
        assert len(mail.outbox) == 0

    def test_student_without_email_skipped(self, db, school, standard, subject, chapter, teacher):
        from openshiksha.apps.core.models import User, UserRole
        from openshiksha.apps.core.tasks import send_due_date_reminders

        no_email = User.objects.create_user(
            username="noemail", password="pass", role=UserRole.STUDENT, school=school, email=""
        )
        _make_assignment(school, standard, subject, chapter, teacher, [no_email], due_in_hours=12)

        stats = send_due_date_reminders()
        assert stats["reminded"] == 0
        assert len(mail.outbox) == 0

    def test_targeted_assignment_reminds_only_target(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.models import User, UserRole
        from openshiksha.apps.core.tasks import send_due_date_reminders

        other = User.objects.create_user(
            username="other_student",
            password="pass",
            role=UserRole.STUDENT,
            school=school,
            email="other@test.example",
        )
        _make_assignment(school, standard, subject, chapter, teacher, [student, other], due_in_hours=12, target=student)

        stats = send_due_date_reminders()
        assert stats["reminded"] == 1
        assert mail.outbox[0].to == ["student@test.example"]

    def test_custom_window_hours(self, db, school, standard, subject, chapter, teacher, student):
        from openshiksha.apps.core.tasks import send_due_date_reminders

        _make_assignment(school, standard, subject, chapter, teacher, [student], due_in_hours=40)

        # Default 24h window misses it; a 48h window catches it.
        assert send_due_date_reminders()["reminded"] == 0
        assert send_due_date_reminders(window_hours=48)["reminded"] == 1
