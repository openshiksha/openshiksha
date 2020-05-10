import argparse
import csv
import os

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http.request import HttpRequest

import openshiksha.settings as settings
from core.models import SchoolProfile
from core.models import UserInfo, Home, SubjectRoom, ClassRoom, Standard, Group, School, Subject, Board
from core.utils.constants import OpenShikshaEnv
from core.utils.references import OpenShikshaGroup
from openshiksha.context_processors import settings as settings_context_processor
from scripts.database.enforcer import enforcer_check
from scripts.email.openshiksha_users import runscript_args_workaround
from scripts.fixtures.dump_data import snapshot_db

# to use this script, run following command from the terminal
# python manage.py runscript scripts.setup.full_school
#
# ensure all the csv files mentioned below are in the same
# folder as the script.

TEXT_BODY_TEMPLATE_NAME = 'activation/text_body.html'
HTML_BODY_TEMPLATE_NAME = 'activation/html_body.html'
SUBJECT_TEMPLATE_NAME = 'activation/email_subject.html'

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'full_school_data')
USER_CSV_PATH = os.path.join(DATA_DIR, 'user.csv')
HOME_CSV_PATH = os.path.join(DATA_DIR, 'home.csv')
CLASSROOM_CSV_PATH = os.path.join(DATA_DIR, 'classroom.csv')
SUBJECTROOM_CSV_PATH = os.path.join(DATA_DIR, 'subjectroom.csv')


SETUP_PASSWORD = os.getenv('OPENSHIKSHA_SETUP_PASSWORD')

def build_username(fname, lname):
    try_count = 0
    username = None
    while True:
        username = fname + '_' + lname + ('' if try_count==0 else str(try_count))
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            break
        try_count += 1

    return username

def get_students(emails):
    students = []
    for student_email in emails.split(','):
        student_email = student_email.strip()
        if student_email == '':
            continue
        student = User.objects.get(email=student_email)
        assert student.userinfo.group == OpenShikshaGroup.refs.STUDENT
        students.append(student)

    print 'Processed students list: %s' % students
    return students


class ContextualPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        # Add some special context
        context.update(settings_context_processor(HttpRequest()))

        super(ContextualPasswordResetForm, self).send_mail(subject_template_name, email_template_name,
                                                           context, from_email, to_email, html_email_template_name)

def send_activation_email(email_id):
    form = ContextualPasswordResetForm({'email': email_id})
    if form.is_valid():
        print "Sending activation email to %s" % email_id
        opts = {
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'email_template_name': TEXT_BODY_TEMPLATE_NAME,
            'html_email_template_name': HTML_BODY_TEMPLATE_NAME,
            'subject_template_name': SUBJECT_TEMPLATE_NAME,
        }

        form.save(**opts)
        print "Email sent"
    else:
        raise ValidationError('Invalid PasswordResetForm for email %s' % form.email)

def run(*args):
    parser = argparse.ArgumentParser(description="Setup a new school for OpenShiksha")
    parser.add_argument('--school', '-s', type=long, required=True, help='id for new school')
    parser.add_argument('--board', '-b', type=long, required=True, help='board id for new school')
    parser.add_argument('--name', '-n', required=True, help='The name of the new school')
    parser.add_argument('--actual', '-a', action='store_true',help='actually send emails (otherwise only database changes are made)' )

    argv = runscript_args_workaround(args)
    processed_args = parser.parse_args(argv)
    print 'Running with args:', processed_args

    snapshot_db()

    # first make sure school does not already exist
    new_school_id = processed_args.school
    try:
        school = School.objects.get(pk=new_school_id)
        raise Exception('Invalid school id: %s Already used for %s' %(new_school_id, school))
    except School.DoesNotExist:
        pass
    # new_school_id - 1 should exist
    existing_school = School.objects.get(pk=new_school_id-1)

    # make the new school entry
    board = Board.objects.get(pk=processed_args.board)
    name = processed_args.name
    root = User.objects.get(username='root')
    new_school = School(name=name, board=board, admin=root)
    new_school.save()

    #create school's admin user entry
    admin = User.objects.create_user(username='openshiksha_admin_school_' + str(new_school_id),
                                     email='openshiksha_admin_school_' + str(new_school_id) + '@openshiksha.org',
                                     password=SETUP_PASSWORD,
                                     first_name='Admin',
                                     last_name='School_' + str(new_school_id))

    # set up admin userinfo
    admin_userinfo = UserInfo(user=admin)
    admin_userinfo.group = OpenShikshaGroup.refs.ADMIN
    admin_userinfo.school = new_school
    admin_userinfo.save()

    # reassign new school's admin
    new_school.admin = admin
    new_school.save()

    # set the new school's profile
    # TODO: incorporate school profile options as command line args
    school_profile = SchoolProfile(school=new_school)
    school_profile.save()

    with open(USER_CSV_PATH) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row['email']
            fname = row['fname']
            lname = row['lname']
            username = build_username(fname, lname)
            group = row['group']
            school = row ['school']
            print "Creating user : %s ,email: %s" % (username, email)
            user = User.objects.create_user(username=username,
                                     email=email,
                                     password=SETUP_PASSWORD)
            user.first_name = fname
            user.last_name = lname
            user.save()
            userinfo = UserInfo(user=user)
            userinfo.group=Group.objects.get(pk=group)
            userinfo.school=School.objects.get(pk=school)
            userinfo.save()
            # TODO: Dossier setup

            if processed_args.actual:
                send_activation_email(email)
            else:
                print "Skipping email sending for dry run"

    print "All users saved!"


    with open(HOME_CSV_PATH) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            parent = User.objects.get(email=row['parent'])
            assert parent.userinfo.group == OpenShikshaGroup.refs.PARENT
            children = get_students(row['children'])
            home = Home(parent=parent)
            print "Adding home for parent : %s" % parent
            home.save()
            for child in children:
                print '\tAdding %s as child' % child
                home.children.add(child)
            home.save()
    print "Added home for all parents"

    with open(CLASSROOM_CSV_PATH) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            classteacher = User.objects.get(email=row['classteacher'])
            assert classteacher.userinfo.group == OpenShikshaGroup.refs.TEACHER
            school = School.objects.get(pk=row['school'])
            standard = Standard.objects.get(number=row['standard'])

            students = get_students(row['students'])
            division = row['division']

            classroom = ClassRoom()
            classroom.classTeacher = classteacher
            classroom.school = school
            classroom.standard = standard
            classroom.division = division
            print "Adding classroom %s with classteacher %s" % (classroom, classteacher)
            classroom.save()
            for student in students:
                print '\tAdding %s as classroom student' % student
                classroom.students.add(student)
            classroom.save()
    print "Added all classrooms"

    with open(SUBJECTROOM_CSV_PATH) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            teacher = User.objects.get(email=row['teacher'])
            assert teacher.userinfo.group == OpenShikshaGroup.refs.TEACHER
            subject = Subject.objects.get(pk=row['subject'])
            classroom = ClassRoom.objects.get(pk=row['classroom'])
            students = get_students(row['students'])
            subjectroom = SubjectRoom()
            subjectroom.teacher = teacher
            subjectroom.subject = subject
            subjectroom.classRoom = classroom
            print "Adding subjectroom %s with subjectteacher %s for classroom %s" % (subjectroom, teacher, classroom)
            subjectroom.save()
            for student in students:
                print '\tAdding %s as subjectroom student' % student
                subjectroom.students.add(student)
            subjectroom.save()
    print "Added all subjectrooms"

    print "\n\nFull-School setup finished\n"

    enforcer_check()
