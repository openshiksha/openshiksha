from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render

from core.forms.password import NonSavingCustomSetPasswordForm
from core.models import School, UserInfo
from core.utils.references import OpenShikshaGroup
from core.utils.toast import render_with_error_toast, render_with_success_toast
from core.utils.user_checks import is_openshiksha_team_admin
from core.view_models.base import AuthenticatedVM
from ink.forms import InkForm
from ink.models import Dossier
from ink.urlnames import InkUrlNames
from ink.view_drivers import ParentIdGet, ParentIdPost
from ink.view_models import IndexBody
from scripts.setup.full_school import build_username

def is_allowed_ink(user):
    if not is_openshiksha_team_admin(user):
        raise Http404
    return True

@login_required
@user_passes_test(is_allowed_ink)
def index_get(request):
    return render(request, InkUrlNames.INDEX.template, AuthenticatedVM(request.user, IndexBody(InkForm(), NonSavingCustomSetPasswordForm())).as_context())


@login_required
@user_passes_test(is_allowed_ink)
def index_post(request):
    ink_form = InkForm(request.POST)
    password_form = NonSavingCustomSetPasswordForm(request.POST)
    if ink_form.is_valid() and password_form.is_valid():
        fname = ink_form.cleaned_data['fname']
        lname = ink_form.cleaned_data['lname']
        email = ink_form.cleaned_data['email']
        classroom = ink_form.cleaned_data['section']

        username = build_username(fname, lname)
        group = OpenShikshaGroup.refs.STUDENT
        school = request.user.userinfo.school

        password = password_form.cleaned_data['new_password2']

        user = User.objects.create_user(username=username,
                                        email=email,
                                        password=password)
        user.first_name = fname
        user.last_name = lname
        user.save()
        userinfo = UserInfo(user=user)
        userinfo.group = group
        userinfo.school = school
        userinfo.save()

        # student has been created, now add the student to the right classroom and subjectrooms
        classroom.students.add(user)
        classroom.save()

        for subjectroom in classroom.subjectroom_set.all():
            subjectroom.students.add(user)
            subjectroom.save()

        # finally, save the dossier on the new user - TODO: part of ink form should be replaced by dossier modelform
        dossier = Dossier(user=user)
        dossier.flagged = ink_form.cleaned_data['flagged']
        dossier.phone = ink_form.cleaned_data['phone']
        if ink_form.cleaned_data['secondaryPhone']:
            dossier.secondaryPhone = ink_form.cleaned_data['secondaryPhone']
        if ink_form.cleaned_data['secondaryEmail']:
            dossier.secondaryEmail = ink_form.cleaned_data['secondaryEmail']

        dossier.save()

        return render_with_success_toast(request,
                                         '<div>The new account has been activated!</div><h3>username: %s</h3>' % username,
                                         InkUrlNames.INDEX.template, AuthenticatedVM(request.user, IndexBody(InkForm(), NonSavingCustomSetPasswordForm())).as_context())
    else:
        return render_with_error_toast(request,
                                       'There was a problem with your information. Please fix the errors and try again.',
                                       InkUrlNames.INDEX.template, AuthenticatedVM(request.user, IndexBody(ink_form, password_form)).as_context())

@login_required
@user_passes_test(is_allowed_ink)
def parent_id_get(request, student_id):
    return ParentIdGet(request, student_id).handle()

@login_required
@user_passes_test(is_allowed_ink)
def parent_id_post(request, student_id):
    return ParentIdPost(request, student_id).handle()