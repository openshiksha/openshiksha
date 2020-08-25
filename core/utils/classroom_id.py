import django
from django.db.models import Avg, Q

from core.models import SubjectRoom, Assignment, Submission
from core.utils.base import BaseUtils
from core.utils.labels import get_focusroom_label
from core.utils.teacher import UncorrectedAssignmentInfoMixin
from focus.models import FocusRoom


class ClassroomIdUtils(UncorrectedAssignmentInfoMixin, BaseUtils):
    def __init__(self, classroom):
        self.classroom = classroom
        super(ClassroomIdUtils, self).__init__(classroom.school)

    def get_contained_room_labels(self):
        rooms = []
        for subjectroom in self.get_contained_subjectrooms():
            rooms.append(subjectroom.subject.name)
            if self.focus:
                rooms.append(get_focusroom_label(subjectroom.subject.name))

        return rooms

    def get_contained_subjectrooms(self):
        return SubjectRoom.objects.filter(classRoom=self.classroom).order_by('subject__name')

    def get_contained_focusrooms(self):
        assert self.focus
        return FocusRoom.objects.filter(subjectRoom__classRoom=self.classroom).order_by('subjectRoom__subject__name')

    def get_contained_subjectroom_ids(self):
        return self.get_contained_subjectrooms().values_list('pk', flat=True)

    def get_contained_focusroom_ids(self):
        return self.get_contained_focusrooms().values_list('pk', flat=True)

    def get_uncorrected_assignments(self):
        now = django.utils.timezone.now()

        filter = Q(subjectRoom__pk__in=self.get_contained_subjectroom_ids())
        if self.focus:
            filter |= Q(remedial__focusRoom__pk__in=self.get_contained_focusroom_ids())

        return Assignment.objects.filter(filter & Q(due__gte=now)).order_by('-due')

    def get_corrected_assignments(self):
        now = django.utils.timezone.now()

        filter = Q(subjectRoom__pk__in=self.get_contained_subjectroom_ids())
        if self.focus:
            filter |= Q(remedial__focusRoom__pk__in=self.get_contained_focusroom_ids())

        return Assignment.objects.filter(filter & Q(due__lte=now) & Q(average__isnull=False)).order_by('-due')

    def get_reportcard_row_info(self):
        results = []
        now = django.utils.timezone.now()
        for student in self.classroom.students.all():
            averages = []
            for subjectroom in self.get_contained_subjectrooms():
                averages.append(Submission.objects.filter(student=student, assignment__subjectRoom=subjectroom,
                                                          assignment__due__lte=now, assignment__average__isnull=False).aggregate(Avg('marks'))[
                                    'marks__avg'])
                if self.focus:
                    averages.append(Submission.objects.filter(student=student,
                                                              assignment__remedial__focusRoom=subjectroom.focusroom,
                                                              assignment__due__lte=now, assignment__average__isnull=False).aggregate(Avg('marks'))[
                                        'marks__avg'])

            filter = Q(assignment__subjectRoom__classRoom=self.classroom)
            if self.focus:
                filter |= Q(assignment__remedial__focusRoom__subjectRoom__classRoom=self.classroom)

            aggregate = \
            Submission.objects.filter(Q(student=student, assignment__due__lte=now, assignment__average__isnull=False) & filter).aggregate(Avg('marks'))[
                'marks__avg']
            results.append((student, averages, aggregate))

        return results

    def get_classroom_averages_by_subject(self):
        results = []
        now = django.utils.timezone.now()
        for subjectroom in self.get_contained_subjectrooms():
            results.append(Assignment.objects.filter(subjectRoom=subjectroom, due__lte=now, average__isnull=False).aggregate(Avg('average'))[
                               'average__avg'])
            if self.focus:
                results.append(
                    Assignment.objects.filter(remedial__focusRoom=subjectroom.focusroom, due__lte=now, average__isnull=False).aggregate(
                        Avg('average'))[
                        'average__avg'])

        return results

    def get_classroom_average(self):
        return self.get_corrected_assignments().aggregate(Avg('average'))['average__avg']
