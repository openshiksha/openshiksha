from django.contrib.contenttypes.models import ContentType

from core.models import School, ClassRoom, SubjectRoom
from core.routing.urlnames import UrlNames
from core.utils.admin import AdminUtils
from core.utils.labels import get_datetime_label, get_classroom_label, get_subjectroom_label, get_percentage_label, \
    get_user_label, get_average_label
from core.utils.student import StudentUtils
from core.utils.teacher import TeacherUtils
from core.view_models.base import AuthenticatedBody
from core.view_models.utils import Link
from hwcentral.exceptions import InvalidHWCentralContentTypeError


class AnnouncementRow(object):
    def __init__(self, announcement):
        self.message = announcement.message
        self.timestamp = get_datetime_label(announcement.timestamp)
        if announcement.content_type == ContentType.objects.get_for_model(School):
            self.target = announcement.content_object.name
        elif announcement.content_type == ContentType.objects.get_for_model(ClassRoom):
            self.target = get_classroom_label(announcement.content_object)
        elif announcement.content_type == ContentType.objects.get_for_model(SubjectRoom):
            self.target = get_subjectroom_label(announcement.content_object)
        else:
            raise InvalidHWCentralContentTypeError(announcement.content_type)


class AssignmentRowBase(object):
    def __init__(self, assignment):
        self.subject = Link(self.get_subjectroom_label(assignment), UrlNames.SUBJECT_ID.name,
                            assignment.subjectRoom.pk)
        self.due = get_datetime_label(assignment.due)

    def get_subjectroom_label(self, assignment):
        raise NotImplementedError("subclass of AssignmentRowBase must implement method get_subjectroom_label")


class StudentSubjectroomLabelMixin(object):
    def get_subjectroom_label(self, assignment):
        return assignment.subjectRoom.subject.name


class TeacherSubjectRoomLabelMixin(object):
    def get_subjectroom_label(self, assignment):
        return get_subjectroom_label(assignment.subjectRoom)


class CorrectedAssignmentRowBase(AssignmentRowBase):
    def __init__(self, assignment):
        super(CorrectedAssignmentRowBase, self).__init__(assignment)
        self.average = get_percentage_label(assignment.average)
        self.assignment_id = assignment.pk

class StudentCorrectedAssignmentRow(StudentSubjectroomLabelMixin, CorrectedAssignmentRowBase):
    def __init__(self, submission):
        super(StudentCorrectedAssignmentRow, self).__init__(submission.assignment)
        self.title = Link(submission.assignment.assignmentQuestionsList.get_title(), UrlNames.SUBMISSION_ID.name,
                          submission.pk)
        self.marks = Link(get_percentage_label(submission.marks), UrlNames.SUBMISSION_ID.name, submission.pk)


class TeacherCorrectedAssignmentRow(TeacherSubjectRoomLabelMixin, CorrectedAssignmentRowBase):
    def __init__(self, assignment):
        super(TeacherCorrectedAssignmentRow, self).__init__(assignment)
        self.title = assignment.assignmentQuestionsList.get_title()


class ActiveAssignmentRow(StudentSubjectroomLabelMixin, AssignmentRowBase):  # used by student, parent
    def __init__(self, active_assignment, completion):
        super(ActiveAssignmentRow, self).__init__(active_assignment)
        self.title = Link(active_assignment.assignmentQuestionsList.get_title(), UrlNames.ASSIGNMENT_ID.name,
                          active_assignment.pk)
        self.completion = Link(get_percentage_label(completion), UrlNames.ASSIGNMENT_ID.name, active_assignment.pk)


class UncorrectedAssignmentRow(TeacherSubjectRoomLabelMixin, AssignmentRowBase):  # used by teacher, admin
    def __init__(self, uncorrected_assignment, is_active, submissions_received):
        super(UncorrectedAssignmentRow, self).__init__(uncorrected_assignment)
        self.title = Link(uncorrected_assignment.assignmentQuestionsList.get_title(), UrlNames.ASSIGNMENT_ID.name,
                          uncorrected_assignment.pk)
        self.opens = get_datetime_label(uncorrected_assignment.assigned)
        self.submissions_received = get_percentage_label(submissions_received)
        self.is_active = is_active


class TeachersTableSubjectroomRow(object):
    def __init__(self, subjectroom, average):
        self.name = Link(get_subjectroom_label(subjectroom), UrlNames.SUBJECT_ID.name, subjectroom.pk)
        self.subjectteacher = get_user_label(subjectroom.teacher)
        self.average = get_average_label(average)


class TeachersTableClassroomRow(object):
    def __init__(self, classroom, subjectroom_rows):
        self.classroom = Link(get_classroom_label(classroom), UrlNames.CLASSROOM_ID.name, classroom.pk)
        self.classteacher = get_user_label(classroom.classTeacher)
        self.subjectroom_rows = subjectroom_rows


class TeachersTable(object):
    def __init__(self, admin, classroom_rows):
        self.school_name = admin.userinfo.school.name
        self.classroom_rows = classroom_rows

class HomeBody(AuthenticatedBody):
    """
    Abstract class that is used to store any common data between the bodies of all the home views
    """
    pass


class StudentHomeBody(HomeBody):
    def __init__(self, user):
        utils = StudentUtils(user)
        self.announcements = [AnnouncementRow(announcement) for announcement in utils.get_announcements()]
        self.username = user.username  # used as suffix on the id for the active assignments table
        self.active_assignments = [ActiveAssignmentRow(active_assignment, completion) for active_assignment, completion
                                   in utils.get_active_assignments_with_completion()]
        self.corrected_assignments = [StudentCorrectedAssignmentRow(submission) for submission in
                                      utils.get_corrected_submissions()]


class TeacherHomeBody(HomeBody):
    def __init__(self, user):
        utils = TeacherUtils(user)
        self.announcements = [AnnouncementRow(announcement) for announcement in utils.get_announcements()]
        self.uncorrected_assignments = [
            UncorrectedAssignmentRow(uncorrected_assignment, is_active, submissions_received)
            for uncorrected_assignment, is_active, submissions_received
            in utils.get_uncorrected_assignments_with_info()]
        self.corrected_assignments = [TeacherCorrectedAssignmentRow(assignment) for assignment in
                                      utils.get_corrected_assignments()]


class ChildHomeBody(StudentHomeBody):
    def __init__(self, child):
        super(ChildHomeBody, self).__init__(child)
        self.name = get_user_label(child)
        self.child_id = child.pk
        self.classroom = get_classroom_label(child.classes_enrolled_set.get())


class ParentHomeBody(HomeBody):
    def __init__(self, user):
        self.child_home_bodies = []
        for child in user.home.children.all():
            self.child_home_bodies.append(ChildHomeBody(child))


class AdminHomeBody(HomeBody):
    def __init__(self, user):
        utils = AdminUtils(user)
        self.announcements = [AnnouncementRow(announcement) for announcement in utils.get_announcements()]
        self.uncorrected_assignments = [
            UncorrectedAssignmentRow(uncorrected_assignment, is_active, submissions_received)
            for uncorrected_assignment, is_active, submissions_received
            in utils.get_uncorrected_assignments_with_info()]
        self.corrected_assignments = [TeacherCorrectedAssignmentRow(assignment) for assignment in
                                      utils.get_corrected_assignments()]
        self.teachers_table = TeachersTable(user, utils.get_teachers_table_classroom_rows())
