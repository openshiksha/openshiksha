from core.utils.admin import AdminUtils
from core.utils.json import OpenShikshaJsonResponse, Json404Response
from core.utils.open_student import OpenStudentUtils
from core.utils.parent import ParentUtils
from core.utils.student import StudentUtils
from core.utils.teacher import TeacherUtils
from core.view_drivers.base import GroupDriven
from core.view_models.ajax import AnnouncementRow, TeacherSubjectRoomSelectElem, \
    StudentSubjectRoomSelectElem, OpenSubjectRoomSelectElem, TeacherSubjectRoomSelectOverrideElem


class GroupDrivenAjax(GroupDriven):
    """
    Abstract class that provides common functionality required by all ajax data endpoints which have different logic
    for different user group
    """
    pass

class AnnouncementsAjaxGet(GroupDrivenAjax):
    @classmethod
    def formatted_response(cls, utils):
        return OpenShikshaJsonResponse([AnnouncementRow(announcement) for announcement in utils.get_announcements()])

    def student_endpoint(self):
        return AnnouncementsAjaxGet.formatted_response(StudentUtils(self.user))

    def teacher_endpoint(self):
        return AnnouncementsAjaxGet.formatted_response(TeacherUtils(self.user))

    def admin_endpoint(self):
        return AnnouncementsAjaxGet.formatted_response(AdminUtils(self.user))

    def parent_endpoint(self):
        return AnnouncementsAjaxGet.formatted_response(ParentUtils(self.user))

    def open_student_endpoint(self):
        return AnnouncementsAjaxGet.formatted_response(OpenStudentUtils(self.user))

class QuestionSetChoiceWidgetAjaxGet(GroupDrivenAjax):
    def __init__(self, request, override):
        self.override=override
        super(QuestionSetChoiceWidgetAjaxGet, self).__init__(request)

    def student_endpoint(self):
        return OpenShikshaJsonResponse([StudentSubjectRoomSelectElem(self.user, subjectroom) for subjectroom in
                                      self.user.subjects_enrolled_set.all()])
    def parent_endpoint(self):
        return Json404Response()
    def admin_endpoint(self):
        return Json404Response()

    def teacher_endpoint(self):
        if self.override:
            return OpenShikshaJsonResponse([TeacherSubjectRoomSelectOverrideElem(subjectroom) for subjectroom in
                                          self.user.subjects_managed_set.all()])
        else:
            return OpenShikshaJsonResponse([TeacherSubjectRoomSelectElem(subjectroom) for subjectroom in
                                      self.user.subjects_managed_set.all()])

    def open_student_endpoint(self):
        return OpenShikshaJsonResponse([OpenSubjectRoomSelectElem(subjectroom) for subjectroom in
                                      self.user.subjects_enrolled_set.all()])
