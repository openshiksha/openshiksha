"""
Tests for email notifications triggered by grading and remedial assignment creation.
"""

from unittest.mock import patch

import pytest

from django.core import mail

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

    return School.objects.create(name="Email Notif School", board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.create(number=8)


@pytest.fixture
def subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard)


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(
        username="email_teacher",
        password="pass",
        role=UserRole.TEACHER,
        school=school,
        email="teacher@school.test",
    )


@pytest.fixture
def student_with_email(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(
        username="email_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        email="student@test.example",
    )


@pytest.fixture
def student_no_email(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(
        username="noemail_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        email="",
    )


@pytest.fixture(autouse=True)
def use_locmem_email(settings):
    """Use the in-memory email backend and clear outbox before each test."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []


# ---------------------------------------------------------------------------
# Email helper unit tests
# ---------------------------------------------------------------------------


class TestEmailHelpers:
    def test_notify_remedial_assigned_sends_email(self, db, student_with_email):
        from openshiksha.apps.core.emails import notify_remedial_assigned

        notify_remedial_assigned(student_with_email, "Algebra", "May 27")

        assert len(mail.outbox) == 1
        assert "practice assignment" in mail.outbox[0].subject
        assert mail.outbox[0].to == ["student@test.example"]
        assert "Algebra" in mail.outbox[0].body
        assert "May 27" in mail.outbox[0].body

    def test_notify_grading_complete_sends_email(self, db, student_with_email):
        from openshiksha.apps.core.emails import notify_grading_complete

        notify_grading_complete(student_with_email, "Chapter 3 Test", 78)

        assert len(mail.outbox) == 1
        assert "graded" in mail.outbox[0].subject
        assert "78%" in mail.outbox[0].subject
        assert mail.outbox[0].to == ["student@test.example"]
        assert "Chapter 3 Test" in mail.outbox[0].body
        assert "78%" in mail.outbox[0].body

    def test_no_email_if_no_email_address(self, db, student_no_email):
        from openshiksha.apps.core.emails import notify_grading_complete, notify_remedial_assigned

        notify_grading_complete(student_no_email, "Test Assignment", 50)
        notify_remedial_assigned(student_no_email, "Algebra", "May 27")

        assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# Localized emails (LA-7): preferred_language = "hi" renders Hindi
# ---------------------------------------------------------------------------


class TestEmailLocalization:
    @pytest.fixture
    def hindi_student(self, db, school):
        from openshiksha.apps.core.models import User, UserRole

        return User.objects.create_user(
            username="hindi_student",
            password="pass",
            role=UserRole.STUDENT,
            school=school,
            email="hindi@test.example",
            first_name="Asha",
            preferred_language="hi",
        )

    def test_remedial_email_in_hindi(self, hindi_student):
        from openshiksha.apps.core.emails import notify_remedial_assigned

        notify_remedial_assigned(hindi_student, "Algebra", "May 27")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "आपके लिए एक नया अभ्यास असाइनमेंट है"
        body = mail.outbox[0].body
        assert "नमस्ते Asha" in body
        # Authored content (chapter name) and dates stay as passed.
        assert "Algebra" in body
        assert "May 27" in body

    def test_grading_email_in_hindi(self, hindi_student):
        from openshiksha.apps.core.emails import notify_grading_complete

        notify_grading_complete(hindi_student, "Chapter 3 Test", 78)

        assert len(mail.outbox) == 1
        assert "जाँच लिया गया है" in mail.outbox[0].subject
        assert "78%" in mail.outbox[0].subject
        assert "स्कोर: 78%" in mail.outbox[0].body
        assert "Chapter 3 Test" in mail.outbox[0].body

    def test_reminder_email_in_hindi(self, hindi_student):
        from openshiksha.apps.core.emails import notify_due_date_reminder

        notify_due_date_reminder(hindi_student, "Chapter 3 Test", "May 27")

        assert len(mail.outbox) == 1
        assert "अंतिम तिथि" in mail.outbox[0].subject
        assert "Chapter 3 Test" in mail.outbox[0].subject
        assert "रिमाइंडर बंद कर सकते हैं" in mail.outbox[0].body

    def test_english_remains_the_default(self, db, student_with_email):
        from openshiksha.apps.core.emails import notify_grading_complete

        assert student_with_email.preferred_language == "en"
        notify_grading_complete(student_with_email, "Chapter 3 Test", 78)

        assert mail.outbox[0].subject == "Your assignment has been graded: 78%"

    def test_unknown_language_falls_back_to_english(self, db, student_with_email):
        from openshiksha.apps.core.emails import notify_grading_complete

        # Bypass model validation deliberately — the catalog must not crash.
        student_with_email.preferred_language = "fr"
        notify_grading_complete(student_with_email, "Chapter 3 Test", 78)

        assert mail.outbox[0].subject == "Your assignment has been graded: 78%"


# ---------------------------------------------------------------------------
# Integration: email sent during grade_submission task
# ---------------------------------------------------------------------------


def _build_submission(student, teacher, school, standard, subject, chapter):
    from django.utils import timezone

    from openshiksha.apps.core.models import (
        Assignment,
        ClassRoom,
        ProblemSet,
        Question,
        QuestionSubpart,
        SubjectRoom,
        Submission,
    )

    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A")
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    subject_room.students.add(student)

    question = Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type="fill_blank",
        difficulty=2,
        created_by=teacher,
    )
    subpart = QuestionSubpart.objects.create(
        question=question,
        index=0,
        question_text="What is 2+2?",
        correct_answer={"answer": "4"},
    )

    problem_set = ProblemSet.objects.create(
        title="Test PS",
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        number=1,
        created_by=teacher,
    )
    problem_set.questions.add(question)

    from datetime import timedelta

    assignment = Assignment.objects.create(
        problem_set=problem_set,
        subject_room=subject_room,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=7),
    )

    # No submitted_at — avoids triggering the post_save signal so grading tests
    # can call grade_submission explicitly without double-running.
    return Submission.objects.create(
        assignment=assignment,
        student=student,
        answers={str(subpart.id): "4"},  # correct answer for fill_blank
    )


class TestGradingEmailIntegration:
    def test_grading_complete_email_sent(self, db, student_with_email, teacher, school, standard, subject, chapter):
        from openshiksha.apps.core.tasks import grade_submission

        submission = _build_submission(student_with_email, teacher, school, standard, subject, chapter)
        grade_submission(submission.pk)

        grading_emails = [m for m in mail.outbox if "graded" in m.subject]
        assert len(grading_emails) == 1
        assert grading_emails[0].to == ["student@test.example"]

    def test_no_email_when_student_has_no_email(
        self, db, student_no_email, teacher, school, standard, subject, chapter
    ):
        from openshiksha.apps.core.tasks import grade_submission

        submission = _build_submission(student_no_email, teacher, school, standard, subject, chapter)
        grade_submission(submission.pk)

        assert len(mail.outbox) == 0

    def test_email_failure_does_not_break_grading(
        self, db, student_with_email, teacher, school, standard, subject, chapter
    ):
        """A send_mail exception must not propagate out of grade_submission."""
        from openshiksha.apps.core.tasks import grade_submission

        submission = _build_submission(student_with_email, teacher, school, standard, subject, chapter)

        with patch("openshiksha.apps.core.emails.send_mail", side_effect=Exception("SMTP down")):
            result = grade_submission(submission.pk)

        submission.refresh_from_db()
        assert submission.score is not None
        assert "score" in result
