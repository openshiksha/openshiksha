from datadog import statsd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.signing import BadSignature
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlsafe_base64_decode

from cabinet import cabinet_api
from cabinet.cabinet_api import SIGNER, ENCODING_SEPERATOR
from core.models import Assignment, SubjectRoom, ClassRoom, AssignmentQuestionsList, Submission
from core.routing.urlnames import UrlNames
from core.utils.assignment import get_assignment_type, is_assignment_corrected, get_student_assignment_submission_type, \
    is_practice_assignment, is_student_assignment, is_open_assignment, is_corrected_open_assignment
from core.utils.constants import OpenShikshaAssignmentType, OpenShikshaStudentAssignmentSubmissionType
from core.utils.json import Json404Response
from core.utils.references import OpenShikshaGroup
from core.utils.user_checks import is_subjectroom_student_relationship, \
    is_subjectteacher
from core.view_drivers.ajax import AnnouncementsAjaxGet, QuestionSetChoiceWidgetAjaxGet
from core.view_drivers.announcement import AnnouncementGet, AnnouncementPost
from core.view_drivers.assignment import AssignmentGet, AssignmentPost
from core.view_drivers.assignment_id import AssignmentIdGetInactive, AssignmentIdGetUncorrected
from core.view_drivers.assignment_preview_id import AssignmentPreviewIdGet
from core.view_drivers.chart import StudentChartGet, CompletionChartGet, SingleFocusStudentChartGet, FocusroomChartGet
from core.view_drivers.chart import SubjectroomChartGet, SingleSubjectStudentChartGet, \
    SubjectTeacherSubjectroomChartGet, ClassTeacherSubjectroomChartGet, AssignmentChartGet, StandardAssignmentChartGet
from core.view_drivers.classroom_id import ClassroomIdGet
from core.view_drivers.focus_id import FocusIdGet
from core.view_drivers.focus_id import ParentFocusIdGet
from core.view_drivers.home import HomeGet, HomePost
from core.view_drivers.password import PasswordGet, PasswordPost
from core.view_drivers.practice import PracticeGet
from core.view_drivers.practice import PracticePost
from core.view_drivers.settings import SettingsGet
from core.view_drivers.subject_id import SubjectIdGet, ParentSubjectIdGet
from core.view_drivers.submission_id import SubmissionIdGetUncorrected, SubmissionIdGetCorrected, \
    SubmissionIdPostUncorrected, SubmissionIdGetStudent, \
    SubmissionIdPostStudent
from core.view_models.index import IndexViewModel
from focus.models import FocusRoom
from openshiksha import settings
from openshiksha.exceptions import InvalidOpenShikshaAssignmentTypeError, InvalidStateError
from openshiksha.settings import LOGIN_REDIRECT_URL


def logout_wrapper(logout_view):
    """
    Redirects to index if already logged out, otherwise proceeds to logout
    """

    def delegate_logout(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect(UrlNames.INDEX.name)
        statsd.increment('core.hits.logout')
        return logout_view(request, *args, **kwargs)

    return delegate_logout


def login_wrapper(login_view):
    """
    Redirects to settings.LOGIN_REDIRECT_URL if already logged in, otherwise proceeds to login
    """

    def delegate_login(request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect(LOGIN_REDIRECT_URL)
        statsd.increment('core.hits.login')
        return login_view(request, *args, **kwargs)

    return delegate_login


@statsd.timed('core.get.index')
def index_get(request):
    """
    View that handles requests to the base url. If user is logged in, redirect to home,
    otherwise render the index page
    """
    statsd.increment('core.hits.get.index')

    if request.user.is_authenticated() and (not settings.SLEEP_MODE):
        return redirect(UrlNames.HOME.name)

    # just display the index template
    return render(request, UrlNames.INDEX.get_template(), IndexViewModel().as_context())

@login_required
@statsd.timed('core.get.home')
def home_get(request):
    statsd.increment('core.hits.get.home')
    return HomeGet(request).handle()


@login_required
@statsd.timed('core.post.home')
def home_post(request):
    statsd.increment('core.hits.post.home')
    return HomePost(request).handle()

@login_required
@statsd.timed('core.get.settings')
def settings_get(request):
    statsd.increment('core.hits.get.settings')
    return SettingsGet(request).handle()


@login_required
@statsd.timed('core.get.subject_id')
def subject_id_get(request, subject_id):
    statsd.increment('core.hits.get.subject_id')
    subjectroom = get_object_or_404(SubjectRoom, pk=subject_id)
    return SubjectIdGet(request, subjectroom).handle()


@login_required
@statsd.timed('core.get.parent_subject_id')
def parent_subject_id_get(request, subject_id, child_id):
    statsd.increment('core.hits.get.parent_subject_id')

    subjectroom = get_object_or_404(SubjectRoom, pk=subject_id)
    child = get_object_or_404(User, pk=child_id)

    if not is_subjectroom_student_relationship(subjectroom, child):
        raise Http404

    return ParentSubjectIdGet(request, subjectroom, child).handle()


@login_required
@statsd.timed('core.get.focus_id')
def focus_id_get(request, focus_id):
    statsd.increment('core.hits.get.focus_id')
    focusroom = get_object_or_404(FocusRoom, pk=focus_id)
    return FocusIdGet(request, focusroom).handle()


@login_required
@statsd.timed('core.get.parent_focus_id')
def parent_focus_id_get(request, focus_id, child_id):
    statsd.increment('core.hits.get.parent_focus_id')

    focusroom = get_object_or_404(FocusRoom, pk=focus_id)
    child = get_object_or_404(User, pk=child_id)

    if not is_subjectroom_student_relationship(focusroom.subjectRoom, child):
        raise Http404

    return ParentFocusIdGet(request, focusroom, child).handle()


@login_required
@statsd.timed('core.get.classroom_id')
def classroom_id_get(request, classroom_id):
    statsd.increment('core.hits.get.classroom_id')
    classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    return ClassroomIdGet(request, classroom).handle()


@login_required
@statsd.timed('core.get.assignment')
def assignment_get(request):
    statsd.increment('core.hits.get.assignment')
    return AssignmentGet(request).handle()


@login_required
@statsd.timed('core.post.assignment')
def assignment_post(request):
    statsd.increment('core.hits.post.assignment')
    return AssignmentPost(request).handle()

@login_required
@statsd.timed('core.get.practice')
def practice_get(request):
    statsd.increment('core.hits.get.practice')
    return PracticeGet(request).handle()


@login_required
@statsd.timed('core.post.practice')
def practice_post(request):
    statsd.increment('core.hits.post.practice')
    return PracticePost(request).handle()


@login_required
@statsd.timed('core.get.assignment_override')
def assignment_override_get(request):
    statsd.increment('core.hits.get.assignment_override')
    return AssignmentGet(request, True).handle()


@login_required
@statsd.timed('core.post.assignment_override')
def assignment_override_post(request):
    statsd.increment('core.hits.post.assignment_override')
    return AssignmentPost(request, True).handle()


@login_required
@statsd.timed('core.get.assignment_preview_id')
def assignment_preview_id_get(request, assignment_questions_list_id):
    statsd.increment('core.hits.get.assignment_preview_id')
    assignment_questions_list = get_object_or_404(AssignmentQuestionsList, pk=assignment_questions_list_id)
    return AssignmentPreviewIdGet(request, assignment_questions_list).handle()


@login_required
@statsd.timed('core.get.assignment_id')
def assignment_id_get(request, assignment_id):
    statsd.increment('core.hits.get.assignment_id')

    assignment = get_object_or_404(Assignment, pk=assignment_id)

    assignment_type = get_assignment_type(assignment)

    if assignment_type == OpenShikshaAssignmentType.STUDENT:
        # Student assignments should not be accessible from assignment_id
        raise Http404
    elif assignment_type == OpenShikshaAssignmentType.INACTIVE:
        return AssignmentIdGetInactive(request, assignment).handle()
    elif assignment_type == OpenShikshaAssignmentType.UNCORRECTED:
        return AssignmentIdGetUncorrected(request, assignment).handle()
    elif assignment_type == OpenShikshaAssignmentType.CORRECTED:
        raise Http404  # Only submissions are viewed after an assignment has been corrected
    else:
        raise InvalidOpenShikshaAssignmentTypeError(assignment_type)


@login_required
@statsd.timed('core.get.submission_id')
def submission_id_get(request, submission_id):
    statsd.increment('core.hits.get.submission_id')

    submission = get_object_or_404(Submission, pk=submission_id)

    assignment_type = get_assignment_type(submission.assignment)

    if assignment_type == OpenShikshaAssignmentType.STUDENT:
        return SubmissionIdGetStudent(request, submission).handle()
    elif assignment_type == OpenShikshaAssignmentType.INACTIVE:
        raise InvalidStateError("Submission %s for inactive assignment %s" % (submission, submission.assignment))
    elif assignment_type == OpenShikshaAssignmentType.UNCORRECTED:
        return SubmissionIdGetUncorrected(request, submission).handle()
    elif assignment_type == OpenShikshaAssignmentType.CORRECTED:
        return SubmissionIdGetCorrected(request, submission).handle()
    else:
        raise InvalidOpenShikshaAssignmentTypeError(assignment_type)


@login_required
@statsd.timed('core.post.submission_id')
def submission_id_post(request, submission_id):
    statsd.increment('core.hits.post.submission_id')

    submission = get_object_or_404(Submission, pk=submission_id)

    # submissions can only be submitted for active+uncorrected/practice+uncorrected assignments
    assignment_type = get_assignment_type(submission.assignment)

    if assignment_type == OpenShikshaAssignmentType.STUDENT:
        submission_type = get_student_assignment_submission_type(submission)
        if submission_type == OpenShikshaStudentAssignmentSubmissionType.CORRECTED:
            raise Http404
        elif submission_type == OpenShikshaStudentAssignmentSubmissionType.UNCORRECTED:
            return SubmissionIdPostStudent(request, submission).handle()
        else:
            raise InvalidOpenShikshaAssignmentTypeError(submission_type)
    elif assignment_type == OpenShikshaAssignmentType.INACTIVE:
        raise InvalidStateError("Submission %s for inactive assignment %s" % (submission, submission.assignment))
    elif assignment_type == OpenShikshaAssignmentType.UNCORRECTED:
        return SubmissionIdPostUncorrected(request, submission).handle()
    elif assignment_type == OpenShikshaAssignmentType.CORRECTED:
        raise Http404
    else:
        raise InvalidOpenShikshaAssignmentTypeError(assignment_type)

@login_required
@statsd.timed('core.chart.student')
def student_chart_get(request, student_id):
    statsd.increment('core.hits.chart.student')

    try:
        student = get_object_or_404(User, pk=student_id)
    except Http404, e:
        return Json404Response(e)
    if student.userinfo.group != OpenShikshaGroup.refs.STUDENT and student.userinfo.group != OpenShikshaGroup.refs.OPEN_STUDENT:
        return Json404Response()

    return StudentChartGet(request, student).handle()


@login_required
@statsd.timed('core.chart.single_subject_student')
def single_subject_student_chart_get(request, student_id, subjectroom_id):
    statsd.increment('core.hits.chart.single_subject_student')

    try:
        student = get_object_or_404(User, pk=student_id)
    except Http404, e:
        return Json404Response(e)
    try:
        subjectroom = get_object_or_404(SubjectRoom, pk=subjectroom_id)
    except Http404, e:
        return Json404Response(e)

    # check if provided student belongs to the provided subjectroom
    if not is_subjectroom_student_relationship(subjectroom, student):
        return Json404Response()

    return SingleSubjectStudentChartGet(request, subjectroom, student).handle()

@login_required
@statsd.timed('core.chart.subjectroom')
def subjectroom_chart_get(request, subjectroom_id):
    statsd.increment('core.hits.chart.subjectroom')
    try:
        subjectroom = get_object_or_404(SubjectRoom, pk=subjectroom_id)
    except Http404, e:
        return Json404Response(e)
    return SubjectroomChartGet(request, subjectroom).handle()


@login_required
@statsd.timed('core.chart.single_focus_student')
def single_focus_student_chart_get(request, student_id, focusroom_id):
    statsd.increment('core.hits.chart.single_focus_student')

    try:
        student = get_object_or_404(User, pk=student_id)
    except Http404, e:
        return Json404Response(e)
    try:
        focusroom = get_object_or_404(FocusRoom, pk=focusroom_id)
    except Http404, e:
        return Json404Response(e)

    # check if provided student belongs to the provided subjectroom
    if not is_subjectroom_student_relationship(focusroom.subjectRoom, student):
        return Json404Response()

    return SingleFocusStudentChartGet(request, focusroom, student).handle()


@login_required
@statsd.timed('core.chart.focusroom')
def focusroom_chart_get(request, focusroom_id):
    statsd.increment('core.hits.chart.focusroom')
    try:
        focusroom = get_object_or_404(FocusRoom, pk=focusroom_id)
    except Http404, e:
        return Json404Response(e)
    return FocusroomChartGet(request, focusroom).handle()

@login_required
@statsd.timed('core.chart.subject_teacher_subjectroom')
def subject_teacher_subjectroom_chart_get(request, subjectteacher_id):
    statsd.increment('core.hits.chart.subject_teacher_subjectroom')

    try:
        subjectteacher = get_object_or_404(User, pk=subjectteacher_id)
    except Http404, e:
        return Json404Response(e)
    if not is_subjectteacher(subjectteacher):
        return Json404Response()

    return SubjectTeacherSubjectroomChartGet(request, subjectteacher).handle()


@login_required
@statsd.timed('core.chart.class_teacher_subjectroom')
def class_teacher_subjectroom_chart_get(request, classteacher_id, classroom_id):
    statsd.increment('core.hits.chart.class_teacher_subjectroom')
    try:
        classteacher = get_object_or_404(User, pk=classteacher_id)
    except Http404, e:
        return Json404Response(e)
    try:
        classroom = get_object_or_404(ClassRoom, pk=classroom_id)
    except Http404, e:
        return Json404Response(e)
    if classroom.classTeacher != classteacher:
        return Json404Response()
    return ClassTeacherSubjectroomChartGet(request, classteacher, classroom).handle()


@login_required
@statsd.timed('core.chart.assignment')
def assignment_chart_get(request, assignment_id):
    statsd.increment('core.hits.chart.assignment')
    try:
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        if is_practice_assignment(assignment):
            raise Http404
        # allow for open assignments if they are corrected
        elif is_open_assignment(assignment):
            if not is_corrected_open_assignment(assignment):
                raise Http404
        else:
            # non-student assignment: only allow for corrected assignments
            if not is_assignment_corrected(assignment):
                raise Http404
    except Http404, e:
        return Json404Response(e)

    return AssignmentChartGet(request, assignment).handle()


@login_required
@statsd.timed('core.chart.completion')
def completion_chart_get(request, assignment_id):
    statsd.increment('core.hits.chart.completion')
    try:
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        if is_student_assignment(assignment):
            raise Http404
    except Http404, e:
        return Json404Response(e)
    return CompletionChartGet(request, assignment).handle()

@login_required
@statsd.timed('core.chart.standard_assignment')
def standard_assignment_chart_get(request, assignment_id):
    statsd.increment('core.hits.chart.standard_assignment')
    try:
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        if is_student_assignment(assignment):
            raise Http404
    except Http404, e:
        return Json404Response(e)
    # only allow for corrected assignments
    if not is_assignment_corrected(assignment):
        return Json404Response()
    return StandardAssignmentChartGet(request, assignment).handle()

@login_required
@statsd.timed('core.ajax.announcements')
def announcements_ajax_get(request):
    statsd.increment('core.hits.ajax.announcements')
    return AnnouncementsAjaxGet(request).handle()

@login_required
@statsd.timed('core.ajax.question_set_choice_widget')
def question_set_choice_widget_ajax_get(request):
    statsd.increment('core.hits.ajax.question_set_choice_widget')
    return QuestionSetChoiceWidgetAjaxGet(request, False).handle()

@login_required
@statsd.timed('core.ajax.question_set_choice_widget_override')
def question_set_choice_widget_override_ajax_get(request):
    statsd.increment('core.hits.ajax.question_set_choice_widget_override')
    return QuestionSetChoiceWidgetAjaxGet(request, True).handle()

@login_required
@statsd.timed('core.post.announcement')
def announcement_post(request):
    statsd.increment('core.hits.post.announcement')
    return AnnouncementPost(request).handle()

@login_required
@statsd.timed('core.get.announcement')
def announcement_get(request):
    statsd.increment('core.hits.get.announcement')
    return AnnouncementGet(request).handle()

@login_required
@statsd.timed('core.get.password')
def password_get(request):
    statsd.increment('core.hits.get.password')
    return PasswordGet(request).handle()


@login_required
@statsd.timed('core.post.password')
def password_post(request):
    statsd.increment('core.hits.post.password')
    return PasswordPost(request).handle()


@login_required
@statsd.timed('core.get.secure_static')
def secure_static_get(request, b64_string):
    statsd.increment('core.hits.get.secure_static')

    # first we decode the signed id
    id_signed = urlsafe_base64_decode(b64_string)

    # then we unsign the id - make sure the url is not tampered
    try:
        id_unsigned = SIGNER.unsign(id_signed)
    except BadSignature:
        raise Http404


    # validation
    username = id_unsigned.split(ENCODING_SEPERATOR)[0]
    if request.user.username != username:
        raise Http404

    # validation passed - send request to static resource server and relay the response
    resource_url = id_unsigned[len(username) + 1:]
    return HttpResponse(cabinet_api.get_static_content(resource_url), content_type='image/jpeg')

def test_500_get(request):
    """
    Used to test server error page
    """
    raise Exception('Testing 500 error page')
