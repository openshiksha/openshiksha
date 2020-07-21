import os
import json
import base64
import re

from django.shortcuts import render
from django.utils.safestring import mark_safe

from core.models import Board, School, Standard, Subject, Question, Chapter, QuestionTag, \
    QuestionSubpart
from core.data_models.question import build_question_subpart_from_data
from core.utils.references import EdgeSpecialTags
from core.utils.json import OpenShikshaJsonResponse
from croupier.constraints import SubpartVariableConstraints
from croupier.croupier_api import deal_subpart
from sphinx.urlnames import SphinxUrlNames

HOME_DIR = os.path.expanduser('~')
OUTPUT_CABINET_PATH = os.path.join(HOME_DIR, 'openshiksha-cabinet')
BASE_FILENAME_NUMBER = 1000000


def decode_base64(data, altchars=b'+/'):
    data = str(data)
    data = re.sub('[^a-zA-Z0-9%s]+'%altchars,'',data)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'=' * (4 - missing_padding)
    return base64.b64decode(data, altchars)

def sphinx_failure_response(message):
    return OpenShikshaJsonResponse({
        'success': False,
        'message': message
    })


def sphinx_success_response(data):
    return OpenShikshaJsonResponse({
        'success': True,
        'payload': data
    })


# TODO: this should actually be a GET?
def deal_post(request):
    request_data = json.loads(request.body)  # ajax post data has to be accessed here instead of request.POST

    if 'subpart' not in request_data:
        return sphinx_failure_response('No subpart data provided')

    subpart_data = request_data['subpart']

    try:
        subpart = build_question_subpart_from_data(subpart_data)
    except Exception, e:
        return sphinx_failure_response('Malformed subpart data: %s' % e)

    variable_constraints_data = subpart_data.get('variable_constraints')

    try:
        variable_constraints = SubpartVariableConstraints(variable_constraints_data)
    except Exception, e:
        return sphinx_failure_response('Malformed variable constraints data: %s' % e)

    try:
        dealt_subpart = deal_subpart(subpart, variable_constraints)
    except Exception, e:
        return sphinx_failure_response('Dealing error: %s' % e)

    # return in form useful for sphinx users
    if variable_constraints_data is not None:
        setattr(dealt_subpart, 'variable_constraints', variable_constraints_data)

    return sphinx_success_response(dealt_subpart)

def sphinx_submit_question_post(request):
    request_data = json.loads(request.body)  # ajax post data has to be accessed here instead of request.POST

    if 'question' not in request_data:
        return sphinx_failure_response('No question data provided')

    question_data = request_data['question']

    board = Board.objects.get(pk=int(question_data['board']))
    school = School.objects.get(pk=int(question_data['school']))
    standard = Standard.objects.get(number=int(question_data['standard']))
    subject = Subject.objects.get(name=question_data['subject'])
    chapter=Chapter.objects.get(name=question_data['chapter'])


    common_path=os.path.join(
        str(board.pk),
        str(school.pk),
        str(standard.number),
        str(subject.pk),
        str(chapter.pk)
    )

    question_path = os.path.join(
        OUTPUT_CABINET_PATH,
        'questions'
    )

    question_subpart_path = os.path.join(
        question_path,
        'raw',
        common_path,
    )

    question_container_path = os.path.join(
        question_path,
        'containers',
        common_path,
    )


    subparts = question_data['subparts']
    for subpart_data in subparts:
        try:
            subpart = build_question_subpart_from_data(subpart_data)
        except Exception, e:
            return sphinx_failure_response('Malformed subpart data: %s' % e)

        variable_constraints_data = subpart_data.get('variable_constraints')

        try:
            variable_constraints = SubpartVariableConstraints(variable_constraints_data)
        except Exception, e:
            return sphinx_failure_response('Malformed variable constraints data: %s' % e)

        try:
            dealt_subpart = deal_subpart(subpart, variable_constraints)
        except Exception, e:
            return sphinx_failure_response('Dealing error: %s' % e)

        # return in form useful for sphinx users
        if variable_constraints_data is not None:
            setattr(dealt_subpart, 'variable_constraints', variable_constraints_data)\

    
    created_question = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)
    for tag in question_data['tags']:
        tag_object = QuestionTag.objects.get(name=tag)
        created_question.tags.add(tag_object.pk)
    subparts_numbering = []
    # this is being done to create a unique filename to save the subpart JSON
    for subpart_data in subparts:
        number_of_files_existing = len([name for name in os.listdir(question_subpart_path) if os.path.isfile(os.path.join(question_subpart_path, name))])
        subpart_unique_name = str(
            number_of_files_existing + BASE_FILENAME_NUMBER)
        subpart_json_name = subpart_unique_name + '.json'
        os.chdir(question_subpart_path)
        subpart_index = int(subpart_data['subpart_index'])
        subpart_object = QuestionSubpart.objects.create(question=created_question, index=subpart_index)
        for tag in subpart_data['tags']:
            tag_object = QuestionTag.objects.get(name=tag)
            subpart_object.tags.add(tag_object.pk)
        with open(subpart_json_name, 'w+') as fp:
            json.dump(subpart_data, fp, indent=4)
        subparts_numbering.append(subpart_unique_name)

    question_dump = {
        'content': question_data['content'],
        'hint': question_data['hint'],
        'subparts': subparts_numbering,
    }
    # Save question JSON

    number_of_files_existing = len([name for name in os.listdir(
        question_container_path) if os.path.isfile(os.path.join(question_container_path, name))])
    container_unique_name = str(
        created_question)
    json_container_name = container_unique_name + '.json'
    os.chdir(question_container_path)
    with open(json_container_name, 'w+') as fp:
        json.dump(question_dump, fp, indent=4)


    # Save images correctly
    images_to_save = question_data['all_images']
    for image_name, image_string in images_to_save.iteritems():
        image_path = os.path.join(
            question_subpart_path,
            'img',
        )
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        os.chdir(image_path)
        image_data = decode_base64(image_string.split(',')[1])
        with open(image_name, 'w+') as f:
            f.write(image_data)

    question_response = {
        'response': 'successfully submitted question'
    }
    return sphinx_success_response(question_response)


def tags_get(request):
    tags_list = [{"name": t.name} for t in QuestionTag.objects.exclude(pk__in=EdgeSpecialTags.refs.PKS).order_by('name')]
    serialized_tags = {
        'tags': mark_safe(json.dumps(tags_list))
    }
    return sphinx_success_response(serialized_tags)


def subjects_from_standard_get(request):
    subjects_list = [{"name": t.name} for t in Subject.objects.all().order_by('name')]
    serialized_subjects = {
        'subjects': mark_safe(json.dumps(subjects_list))
    }
    return sphinx_success_response(serialized_subjects)


def chapters_from_subject_get(request):
    subjects_list = [{"name": t.name}
                    for t in Chapter.objects.all().order_by('name')]
    serialized_chapters = {
        'chapters': mark_safe(json.dumps(subjects_list))
    }
    return sphinx_success_response(serialized_chapters)
