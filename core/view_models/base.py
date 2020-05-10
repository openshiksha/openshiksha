from core.utils.admin import AdminUtils
from core.utils.constants import VIEWMODEL_KEY
from core.utils.open_student import OpenStudentUtils
from core.utils.parent import ParentUtils
from core.utils.references import OpenShikshaGroup
from core.utils.student import StudentUtils
from core.utils.teacher import TeacherUtils
from core.view_models.userinfo import HeaderUserInfo
from openshiksha.exceptions import InvalidOpenShikshaGroupError
from lodge.lodge_api import get_video_uri


class VM(object):
    """
    Abstract class that is used to provide as_context functionality to page-level view models
    """

    def as_context(self):
        return {VIEWMODEL_KEY: self}


class FormViewModel(VM):
    def __init__(self, form, form_action_url_name):
        self.form = form
        self.form.action_url_name = form_action_url_name

class AuthenticatedBody(object):
    """
    Abstract class that is used to store any common data between the bodies of all the authenticated views
    """


class AuthenticatedVM(VM):
    """
    Class that is used to provide sidebar view model to all page-level view models for authenticated pages
    """

    def __init__(self, user, authenticated_body):
        from core.view_models.sidebar import AdminSidebar, TeacherSidebar, ParentSidebar, StudentSidebar, \
            OpenStudentSidebar

        if user.userinfo.group == OpenShikshaGroup.refs.STUDENT:
            self.sidebar = StudentSidebar(user)
            utils = StudentUtils(user)
            help_uri = get_video_uri(2)
        elif user.userinfo.group == OpenShikshaGroup.refs.PARENT:
            self.sidebar = ParentSidebar(user)
            utils = ParentUtils(user)
            help_uri = get_video_uri(3)
        elif user.userinfo.group == OpenShikshaGroup.refs.TEACHER:
            self.sidebar = TeacherSidebar(user)
            utils = TeacherUtils(user)
            help_uri = get_video_uri(4)
        elif user.userinfo.group == OpenShikshaGroup.refs.ADMIN:
            self.sidebar = AdminSidebar(user)
            utils = AdminUtils(user)
            help_uri = get_video_uri(5)
        elif user.userinfo.group == OpenShikshaGroup.refs.OPEN_STUDENT:
            self.sidebar = OpenStudentSidebar(user)
            utils = OpenStudentUtils(user)
            help_uri = get_video_uri(6)

        else:
            raise InvalidOpenShikshaGroupError(user.userinfo.group)

        self.userinfo = HeaderUserInfo(user, utils.get_announcements_count(), help_uri)
        self.authenticated_body = authenticated_body


class BaseFormBody(AuthenticatedBody):
    """
    Abstract class that provides the most basic functionality for a form-defined viewmodel -> it wraps a form object
    """

    def __init__(self, form):
        self.form = form


class FormBody(BaseFormBody):
    """
    Abstract class that is used to store common logic for all form view models
    """

    def __init__(self, form, form_action_url_name):
        """
        @param form: django form object that the template this viewmodel is passed to will render
        @param form_action_url_name: url name for the POST endpoint for the form of this body
        """
        super(FormBody, self).__init__(form)
        self.form.action_url_name = form_action_url_name


class ReadOnlyFormBody(BaseFormBody):
    """
    Assumes that the form passed in has the read-only functionality and applies it so that a read-only form can be rendered
    """
    pass