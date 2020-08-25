import django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from core.models import Assignment, Submission, School, ClassRoom, SubjectRoom
from core.utils.base import UserUtils
from core.utils.references import OpenShikshaGroup
from focus.models import Remedial


class StudentUtils(UserUtils):
    def __init__(self, student):
        self.UTILS_GROUP = OpenShikshaGroup.refs.STUDENT
        super(StudentUtils, self).__init__(student)

    def get_num_unfinished_assignments(self):
        # check if 100% submissions have been posted for each assignment
        num_unfinished_assignments = 0
        for assignment in self.get_active_assignments():
            completion = get_active_assignment_completion(self.user, assignment)
            if completion < 1:
                num_unfinished_assignments += 1

        return num_unfinished_assignments

    def get_enrolled_subjectroom_ids(self):
        return self.user.subjects_enrolled_set.values_list('pk', flat=True)

    def get_enrolled_remedial_ids(self):
        assert self.focus
        return self.user.remedials_enrolled_set.values_list('pk', flat=True)

    def get_active_assignments(self):
        now = django.utils.timezone.now()

        filter = Q(subjectRoom__pk__in=self.get_enrolled_subjectroom_ids())
        if self.focus:
            filter |= Q(remedial__pk__in=self.get_enrolled_remedial_ids())

        return Assignment.objects.filter(filter & Q(due__gte=now) & Q(assigned__lte=now)).order_by('-due')

    def get_announcements_query(self):
        school_type = ContentType.objects.get_for_model(School)
        classroom_type = ContentType.objects.get_for_model(ClassRoom)
        subjectroom_type = ContentType.objects.get_for_model(SubjectRoom)
        student_subjectroom_ids = self.get_enrolled_subjectroom_ids()
        user_type = ContentType.objects.get_for_model(User)
        target_condition = (
            Q(content_type=school_type, object_id=self.user.userinfo.school.pk) |
            Q(content_type=classroom_type, object_id=self.user.classes_enrolled_set.get().pk) |
            Q(content_type=subjectroom_type, object_id__in=student_subjectroom_ids) |
            Q(content_type=user_type, object_id=self.user.pk)
        )

        return (target_condition & StudentUtils.RECENT_ANNOUNCEMENT_CONDITION)


    def get_active_assignments_with_completion(self):
        result = []
        for active_assignment in self.get_active_assignments():
            completion = get_active_assignment_completion(self.user, active_assignment)
            result.append((active_assignment, completion))
        return result

    def get_corrected_submissions(self):
        now = django.utils.timezone.now()

        filter = Q(assignment__content_type=ContentType.objects.get_for_model(SubjectRoom))
        if self.focus:
            filter |= Q(assignment__content_type=ContentType.objects.get_for_model(Remedial))

        return Submission.objects.filter(Q(student=self.user) & Q(assignment__due__lte=now) & Q(assignment__average__isnull=False) & filter).order_by(
            '-assignment__due')

    def get_practice_submissions(self):
        return Submission.objects.filter(student=self.user,
                                         assignment__content_type=ContentType.objects.get_for_model(User),
                                         assignment__object_id=self.user.pk).order_by('-assignment__due')

def get_active_assignment_completion(student, active_assignment):
    try:
        submission = Submission.objects.get(student=student, assignment=active_assignment)
        return submission.completion
    except Submission.DoesNotExist:
        return 0.0


class StudentSubjectIdUtils(StudentUtils):
    def __init__(self, student, subjectroom):
        super(StudentSubjectIdUtils, self).__init__(student)
        self.subjectroom = subjectroom

    def get_active_assignments(self):
        now = django.utils.timezone.now()

        return Assignment.objects.filter(subjectRoom=self.subjectroom, due__gte=now,
                                         assigned__lte=now).order_by('-due')

    def get_corrected_submissions(self):
        now = django.utils.timezone.now()
        return Submission.objects.filter(student=self.user, assignment__subjectRoom=self.subjectroom,
                                         assignment__due__lte=now, assignment__average__isnull=False).order_by('-assignment__due')


class StudentFocusIdUtils(StudentUtils):
    def __init__(self, student, focusroom):
        super(StudentFocusIdUtils, self).__init__(student)
        assert self.focus
        self.focusroom = focusroom

    def get_active_assignments(self):
        now = django.utils.timezone.now()

        active_assignments = []
        for assignment in Assignment.objects.filter(remedial__focusRoom=self.focusroom, due__gte=now,
                                                    assigned__lte=now).order_by('-due'):
            if self.user in assignment.content_object.students.all():
                active_assignments.append(assignment)

        return active_assignments

    def get_corrected_submissions(self):
        now = django.utils.timezone.now()
        return Submission.objects.filter(student=self.user, assignment__remedial__focusRoom=self.focusroom,
                                         assignment__due__lte=now, assignment__average__isnull=False).order_by('-assignment__due')
