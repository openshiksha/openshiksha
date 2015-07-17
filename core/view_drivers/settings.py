from django.shortcuts import render

from core.routing.urlnames import UrlNames
from core.view_models.base import AuthenticatedBase
from core.view_models.settings import StudentSettingsBody, TeacherSettingsBody, ParentSettingsBody, AdminSettingsBody
from core.view_models.sidebar import StudentSidebar, TeacherSidebar, ParentSidebar, AdminSidebar
from core.view_drivers.base import GroupDrivenViewGroupDrivenTemplate


class SettingsGet(GroupDrivenViewGroupDrivenTemplate):
    def __init__(self, request):
        super(SettingsGet, self).__init__(request)
        self.urlname = UrlNames.SETTINGS


    def student_endpoint(self):
        return render(self.request, self.template,
                      AuthenticatedBase(StudentSidebar(self.user), StudentSettingsBody(self.user))
                      .as_context())

    def teacher_endpoint(self):
        return render(self.request, self.template,
                      AuthenticatedBase(TeacherSidebar(self.user), TeacherSettingsBody(self.user))
                      .as_context())

    def parent_endpoint(self):
        return render(self.request, self.template,
                      AuthenticatedBase(ParentSidebar(self.user), ParentSettingsBody(self.user))
                      .as_context())

    def admin_endpoint(self):
        return render(self.request, self.template,
                      AuthenticatedBase(AdminSidebar(self.user), AdminSettingsBody(self.user))
                      .as_context())