from django.conf.urls import url, include
from django.contrib.auth.views import password_reset_complete, password_reset_confirm, password_reset_done, \
    password_reset, LoginView, logout

from challenge.urlnames import ChallengeUrlNames
from challenge.views import index_get as challenge_index_get
from core.forms.password import CustomSetPasswordForm
from core.routing.routers import dynamic_router, REDIRECT_EXPLICIT_ARGS_KEY, redirect_router, static_authenticated_csrf_cookie_router, static_router, static_authenticated_router
from core.routing.urlnames import UrlNames
from core.utils.constants import HttpMethod
from core.views import home_get, settings_get, subject_id_get, classroom_id_get, \
    parent_subject_id_get, assignment_id_get, assignment_preview_id_get, student_chart_get, \
    single_subject_student_chart_get, subjectroom_chart_get, subject_teacher_subjectroom_chart_get, \
    class_teacher_subjectroom_chart_get, assignment_chart_get, standard_assignment_chart_get, announcement_get, \
    announcement_post, password_get, password_post, submission_id_get, submission_id_post, assignment_get, \
    assignment_post, assignment_override_get, assignment_override_post, secure_static_get, announcements_ajax_get, \
    question_set_choice_widget_override_ajax_get, question_set_choice_widget_ajax_get, completion_chart_get, \
    parent_focus_id_get, focus_id_get, single_focus_student_chart_get, focusroom_chart_get, practice_get, practice_post, \
    home_post
from edge.urlnames import EdgeUrlNames
from edge.views import index_get as edge_index_get, subject_id_get as edge_subject_id_get, \
    student_id_get as edge_student_id_get
from openshiksha.settings import OVERVIEW_VIDEO_PK
from ink.urlnames import InkUrlNames
from ink.views import index_get as ink_index_get, index_post as ink_index_post, parent_id_get, parent_id_post
from lodge.urlnames import LodgeUrlNames
from lodge.views import index_get as lodge_index_get
from openshiksha.urls.common import get_all_mode_urlpatterns
from django.contrib import admin
from sphinx.urlnames import SphinxUrlNames
from sphinx.views import deal_post, tags_get, sphinx_submit_question_post, subjects_from_standard_get, chapters_from_subject_get, fetch_questions
from frontend.urlnames import FrontendUrlNames

from openshiksha.settings import ENVIRON, DEBUG
from core.utils.constants import OpenShikshaEnv
if ENVIRON == OpenShikshaEnv.LOCAL:
    SUCCESS_URL_ALLOWED_HOSTS = {'localhost:3000', '127.0.0.1:3000'}
else:
    SUCCESS_URL_ALLOWED_HOSTS = {}

def get_ink_urlpatterns():
    return [
        url(InkUrlNames.INDEX.url_matcher, dynamic_router,
            {HttpMethod.GET: ink_index_get, HttpMethod.POST: ink_index_post},
            name=InkUrlNames.INDEX.name),
        url(InkUrlNames.PARENT_ID.url_matcher, dynamic_router, {HttpMethod.GET: parent_id_get, HttpMethod.POST: parent_id_post}, name=InkUrlNames.PARENT_ID.name)
    ]


def get_edge_urlpatterns():
    return [
        url(EdgeUrlNames.INDEX.url_matcher, dynamic_router, {HttpMethod.GET: edge_index_get},
            name=EdgeUrlNames.INDEX.name),
        url(EdgeUrlNames.SUBJECT_ID.url_matcher, dynamic_router, {HttpMethod.GET: edge_subject_id_get},
            name=EdgeUrlNames.SUBJECT_ID.name),
        url(EdgeUrlNames.STUDENT_ID.url_matcher, dynamic_router, {HttpMethod.GET: edge_student_id_get},
            name=EdgeUrlNames.STUDENT_ID.name)

    ]

def get_admin_urlpatterns():
    return [
        url('^admin/doc/', include('django.contrib.admindocs.urls')),
        url('^admin/', include(admin.site.urls)),
    ]


def get_sphinx_urlpatterns():
    return [
        # url(SphinxUrlNames.INDEX.url_matcher, static_authenticated_csrf_cookie_router, {'template': SphinxUrlNames.INDEX.template},
            # name=SphinxUrlNames.INDEX.name),
        url(SphinxUrlNames.DEAL.url_matcher, dynamic_router, {HttpMethod.POST: deal_post},
            name=SphinxUrlNames.DEAL.name),
        url(SphinxUrlNames.SUBMIT_QUESTION.url_matcher, dynamic_router, {HttpMethod.POST: sphinx_submit_question_post},
            name=SphinxUrlNames.SUBMIT_QUESTION.name),
        url(SphinxUrlNames.TAGS.url_matcher, dynamic_router, {HttpMethod.GET: tags_get},
            name=SphinxUrlNames.TAGS.name),
        url(SphinxUrlNames.SUBJECTS_FROM_STANDARD.url_matcher, dynamic_router, {HttpMethod.GET: subjects_from_standard_get},
            name=SphinxUrlNames.SUBJECTS_FROM_STANDARD.name),
        url(SphinxUrlNames.CHAPTERS_FROM_SUBJECT.url_matcher, dynamic_router, {HttpMethod.GET: chapters_from_subject_get },
            name=SphinxUrlNames.CHAPTERS_FROM_SUBJECT.name),
        url(SphinxUrlNames.FETCH_QUESTIONS.url_matcher, dynamic_router, {HttpMethod.GET: fetch_questions},
            name=SphinxUrlNames.FETCH_QUESTIONS.name),
        # url(SphinxUrlNames.REVISION.url_matcher, static_authenticated_router, {'template': SphinxUrlNames.REVISION.template},
            # name=SphinxUrlNames.REVISION.name)
    ]

def get_frontend_urlpatterns():
    return [
        url(FrontendUrlNames.INDEX.url_matcher, static_authenticated_csrf_cookie_router, {'template': FrontendUrlNames.INDEX.template},
            name=FrontendUrlNames.INDEX.name),
    ]


def get_regular_mode_urlpatterns():
    regular_mode_urlpatterns = get_all_mode_urlpatterns() \
        + get_ink_urlpatterns() \
        + get_edge_urlpatterns() \
        + get_admin_urlpatterns() \
        + get_sphinx_urlpatterns() \
        + get_frontend_urlpatterns()

    regular_mode_urlpatterns += [
        # using django's inbuilt auth views for auth-specific tasks
        url(UrlNames.LOGIN.url_matcher, LoginView.as_view(
            template_name=UrlNames.LOGIN.get_template(),
            redirect_authenticated_user=True,
            success_url_allowed_hosts=SUCCESS_URL_ALLOWED_HOSTS
        ), name=UrlNames.LOGIN.name),

        url(UrlNames.LOGOUT.url_matcher, logout,
            {'next_page': UrlNames.INDEX.name},
            name=UrlNames.LOGOUT.name),

        url(r'^forgot-password/$', password_reset, {
            'template_name': 'forgot_password/form.html',
            'html_email_template_name': 'forgot_password/html_body.html',
            'email_template_name': 'forgot_password/text_body.html',
            'subject_template_name': 'forgot_password/email_subject.html'
        },
            name="forgot_password"),

        url(r'^forgot-password/mailed/$', password_reset_done, {
            'template_name': 'forgot_password/mailed.html'
        },
            name="password_reset_done"),

        #
        # used by both activation script and forgot passsword
        #
        url(r'^password-reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm, {
            'template_name': 'password_reset/form.html',
            'set_password_form': CustomSetPasswordForm
        },
            name="password_reset"),

        url(r'^password-reset/complete/$', password_reset_complete,
            {'template_name': 'password_reset/complete.html'},
            name="password_reset_complete"),
    ]

    if DEBUG:
        import debug_toolbar
        regular_mode_urlpatterns += [
            url('^__debug__/', include(debug_toolbar.urls)),
        ]

    # Adding the core-app urls
    regular_mode_urlpatterns += [
        url(UrlNames.HOME.url_matcher, dynamic_router, {HttpMethod.GET: home_get, HttpMethod.POST: home_post},
            name=UrlNames.HOME.name),

        url(UrlNames.SETTINGS.url_matcher, dynamic_router, {HttpMethod.GET: settings_get},
            name=UrlNames.SETTINGS.name),

        url(UrlNames.SUBJECT_ID.url_matcher, dynamic_router, {HttpMethod.GET: subject_id_get},
            name=UrlNames.SUBJECT_ID.name),
        url(UrlNames.PARENT_SUBJECT_ID.url_matcher, dynamic_router,
            {HttpMethod.GET: parent_subject_id_get},
            name=UrlNames.PARENT_SUBJECT_ID.name),

        url(UrlNames.FOCUS_ID.url_matcher, dynamic_router, {HttpMethod.GET: focus_id_get},
            name=UrlNames.FOCUS_ID.name),
        url(UrlNames.PARENT_FOCUS_ID.url_matcher, dynamic_router,
            {HttpMethod.GET: parent_focus_id_get},
            name=UrlNames.PARENT_FOCUS_ID.name),

        url(UrlNames.CLASSROOM_ID.url_matcher, dynamic_router, {HttpMethod.GET: classroom_id_get},
            name=UrlNames.CLASSROOM_ID.name),

        url(UrlNames.ASSIGNMENT_ID.url_matcher, dynamic_router, {HttpMethod.GET: assignment_id_get},
            name=UrlNames.ASSIGNMENT_ID.name),
        url(UrlNames.ASSIGNMENT_PREVIEW_ID.url_matcher, dynamic_router,
            {HttpMethod.GET: assignment_preview_id_get},
            name=UrlNames.ASSIGNMENT_PREVIEW_ID.name),

        url(UrlNames.SUBMISSION_ID.url_matcher, dynamic_router, {HttpMethod.GET: submission_id_get,
                                                                 HttpMethod.POST: submission_id_post},
            name=UrlNames.SUBMISSION_ID.name),

        url(UrlNames.STUDENT_CHART.url_matcher, dynamic_router, {HttpMethod.GET: student_chart_get},
            name=UrlNames.STUDENT_CHART.name),
        url(UrlNames.SINGLE_SUBJECT_STUDENT_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: single_subject_student_chart_get},
            name=UrlNames.SINGLE_SUBJECT_STUDENT_CHART.name),
        url(UrlNames.SINGLE_FOCUS_STUDENT_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: single_focus_student_chart_get},
            name=UrlNames.SINGLE_FOCUS_STUDENT_CHART.name),
        url(UrlNames.SUBJECTROOM_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: subjectroom_chart_get},
            name=UrlNames.SUBJECTROOM_CHART.name),
        url(UrlNames.FOCUSROOM_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: focusroom_chart_get},
            name=UrlNames.FOCUSROOM_CHART.name),
        url(UrlNames.SUBJECT_TEACHER_SUBJECTROOM_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: subject_teacher_subjectroom_chart_get},
            name=UrlNames.SUBJECT_TEACHER_SUBJECTROOM_CHART.name),
        url(UrlNames.CLASS_TEACHER_SUBJECTROOM_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: class_teacher_subjectroom_chart_get},
            name=UrlNames.CLASS_TEACHER_SUBJECTROOM_CHART.name),
        url(UrlNames.ASSIGNMENT_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: assignment_chart_get},
            name=UrlNames.ASSIGNMENT_CHART.name),
        url(UrlNames.COMPLETION_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: completion_chart_get},
            name=UrlNames.COMPLETION_CHART.name),
        url(UrlNames.STANDARD_ASSIGNMENT_CHART.url_matcher, dynamic_router,
            {HttpMethod.GET: standard_assignment_chart_get},
            name=UrlNames.STANDARD_ASSIGNMENT_CHART.name),


        url(UrlNames.ANNOUNCEMENTS_AJAX.url_matcher, dynamic_router, {HttpMethod.GET: announcements_ajax_get}, name=UrlNames.ANNOUNCEMENTS_AJAX.name),
        url(UrlNames.QUESTION_SET_CHOICE_WIDGET_AJAX.url_matcher, dynamic_router, {HttpMethod.GET: question_set_choice_widget_ajax_get}, name=UrlNames.QUESTION_SET_CHOICE_WIDGET_AJAX.name),
        url(UrlNames.QUESTION_SET_CHOICE_WIDGET_OVERRIDE_AJAX.url_matcher, dynamic_router, {HttpMethod.GET: question_set_choice_widget_override_ajax_get}, name=UrlNames.QUESTION_SET_CHOICE_WIDGET_OVERRIDE_AJAX.name),



        url(UrlNames.ANNOUNCEMENT.url_matcher, dynamic_router, {HttpMethod.GET: announcement_get,
                                                                HttpMethod.POST: announcement_post},
            name=UrlNames.ANNOUNCEMENT.name),
        url(UrlNames.PRACTICE.url_matcher, dynamic_router, {HttpMethod.GET: practice_get,
                                                            HttpMethod.POST: practice_post},
            name=UrlNames.PRACTICE.name),

        url(UrlNames.PASSWORD.url_matcher, dynamic_router, {HttpMethod.GET: password_get,
                                                            HttpMethod.POST: password_post},
            name=UrlNames.PASSWORD.name),

        url(UrlNames.ASSIGNMENT.url_matcher, dynamic_router, {HttpMethod.GET: assignment_get,
                                                              HttpMethod.POST: assignment_post},
            name=UrlNames.ASSIGNMENT.name),
        url(UrlNames.ASSIGNMENT_OVERRIDE.url_matcher, dynamic_router,
            {HttpMethod.GET: assignment_override_get,
             HttpMethod.POST: assignment_override_post},
            name=UrlNames.ASSIGNMENT_OVERRIDE.name),
    ]

    return regular_mode_urlpatterns

urlpatterns = get_regular_mode_urlpatterns()
