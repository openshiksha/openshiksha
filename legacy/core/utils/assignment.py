import django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from core.utils.constants import OpenShikshaAssignmentType, OpenShikshaStudentAssignmentSubmissionType
from core.utils.references import OpenShikshaGroup
from openshiksha.exceptions import InvalidStateError, InvalidContentTypeError


def is_assignment_active(assignment):
    return assignment.assigned < django.utils.timezone.now()


def is_assignment_corrected(assignment):
    return (assignment.due < django.utils.timezone.now()) and (assignment.average is not None)

def get_assignment_type(assignment):
    if is_student_assignment(assignment):
        return OpenShikshaAssignmentType.STUDENT

    if not is_assignment_active(assignment):
        return OpenShikshaAssignmentType.INACTIVE

    if not is_assignment_corrected(assignment):
        return OpenShikshaAssignmentType.UNCORRECTED

    return OpenShikshaAssignmentType.CORRECTED


def is_student_assignment(assignment):
    return assignment.content_type == ContentType.objects.get_for_model(User)


def is_practice_assignment(assignment):
    return is_student_assignment(assignment) and (
    assignment.content_object.userinfo.group == OpenShikshaGroup.refs.STUDENT)


def is_corrected_practice_assignment(assignment):
    return is_practice_assignment(assignment) and (assignment.average is not None)


def is_open_assignment(assignment):
    return is_student_assignment(assignment) and (
    assignment.content_object.userinfo.group == OpenShikshaGroup.refs.OPEN_STUDENT)


def is_corrected_open_assignment(assignment):
    return is_open_assignment(assignment) and (assignment.average is not None)


def get_student_assignment_submission_type(submission):
    assert is_student_assignment(submission.assignment)

    if (submission.marks is not None) and (submission.assignment.average is not None):
        return OpenShikshaStudentAssignmentSubmissionType.CORRECTED
    elif (submission.marks is None) and (submission.assignment.average is None):
        return OpenShikshaStudentAssignmentSubmissionType.UNCORRECTED
    else:
        raise InvalidStateError(
            "Student Assignment Submission %s has only one of marks and assignment average non null" % submission)


def check_homework_assignment(assignment):
    """
    checks that the given assignment is homework for a subjectroom or remedial
    """
    from core.models import SubjectRoom
    from focus.models import Remedial

    if assignment.content_type == ContentType.objects.get_for_model(User):
        raise InvalidStateError("Practice/Open assignment is not a homework assignment.")
    elif (assignment.content_type != ContentType.objects.get_for_model(Remedial)) and (
                assignment.content_type != ContentType.objects.get_for_model(SubjectRoom)):
        raise InvalidContentTypeError(assignment.content_type)
