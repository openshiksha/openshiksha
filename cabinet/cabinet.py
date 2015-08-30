# This file provides the utility methods to access files from the hwcentral-cabinet repository
# The access urls are built differently depending on the hwcentral settings DEBUG flag
import base64
import json
import os

from datadog import statsd
from django.core.signing import Signer
from django.utils.http import urlsafe_base64_encode
import requests

from core.utils.constants import HWCentralQuestionDataType
from core.utils.json import HWCentralJSONEncoder
from core.data_models.question import QuestionContainer, QuestionDM, build_question_part_from_data
from core.data_models.submission import SubmissionDM
from hwcentral import settings
from hwcentral.exceptions import CabinetSubmissionExistsException, CabinetSubmissionMissingException

GITHUB_HEADERS = {
    'Authorization': 'token a7823130e1c75e9541134aa742f26346a0d6ead8',
    'Accept': 'application/vnd.github.v3.object'
}

CABINET_GITHUB_ENDPOINT = 'https://api.github.com/repos/oasisvali/hwcentral-cabinet/contents/'
CABINET_NGINX_ENDPOINT = 'http://localhost:8878/'

# extra flag so that github ep can be enabled/disabled without touching settings.DEBUG
# change True to False to force-disable CABINET_DEBUG
CABINET_DEBUG = settings.DEBUG and True

SECURE_STATIC_ENDPOINT = 'secure-static'

if CABINET_DEBUG:
    CABINET_ENDPOINT = CABINET_GITHUB_ENDPOINT
    HEADERS = GITHUB_HEADERS
    SECURE_STATIC_URL = os.path.join('http://localhost:8000', SECURE_STATIC_ENDPOINT)
else:
    CABINET_ENDPOINT = CABINET_NGINX_ENDPOINT
    HEADERS = {}
    SECURE_STATIC_URL = os.path.join('http://hwcentral.in', SECURE_STATIC_ENDPOINT)

CONFIG_FILE_EXTENSION = '.json'
ENCODING_SEPERATOR = ':'

SIGNER = Signer()
ENCODER = HWCentralJSONEncoder(indent=2)


def build_config_filename(id):
    return str(id) + CONFIG_FILE_EXTENSION

def build_question_url_stub(question, question_data_type):
    return os.path.join(CABINET_ENDPOINT, 'questions', question_data_type,
                        str(question.school.board.pk),
                        str(question.school.pk),
                        str(question.standard.number),
                        str(question.subject.pk),
                        str(question.chapter.pk))


def build_question_data_url(question, question_data_type, question_id):
    return os.path.join(build_question_url_stub(question, question_data_type),
                        build_config_filename(question_id))


def get_resource(url):
    return requests.get(url, headers=HEADERS)


def get_resource_content(url):
    if CABINET_DEBUG:
        return json.loads(base64.b64decode((get_resource(url)).json()['content']))
    else:
        return (get_resource(url)).json()


@statsd.timed('cabinet.get.static')
def get_static_content(url):
    if CABINET_DEBUG:
        return base64.b64decode((get_resource(url)).json()['content'])
    else:
        return get_resource(url)


def get_resource_sha(url):
    return (get_resource(url)).json()['sha']


def get_resource_exists(url):
        return get_resource(url).status_code == 200


def get_question(question):
    # NOTE: cannot just use the Question's from_data method as we dont have all the data available in one dictionary.
    # it must first be aggregated by looking at the container in cabinet
    container_url = build_question_data_url(question, HWCentralQuestionDataType.CONTAINER, question.pk)
    container = QuestionContainer(get_resource_content(container_url))

    subparts = []
    for i, subpart in enumerate(container.subparts):
        subpart_url = build_question_data_url(question, HWCentralQuestionDataType.SUBPART, subpart)
        subpart_data = get_resource_content(subpart_url)

        question_part = build_question_part_from_data(subpart_data)

        assert i == question_part.subpart_index
        subparts.append(question_part)

    return QuestionDM(question.pk, container, subparts)


def build_submission_data_url(submission):
    return os.path.join(CABINET_ENDPOINT, 'submissions',
                        str(submission.assignment.subjectRoom.classRoom.school.pk),
                        str(submission.assignment.subjectRoom.classRoom.standard.number),
                        submission.assignment.subjectRoom.classRoom.division,
                        str(submission.assignment.subjectRoom.subject.pk),
                        str(submission.assignment.pk),
                        build_config_filename(submission.pk))


@statsd.timed('cabinet.get.submission')
def get_submission(submission):
    submission_url = build_submission_data_url(submission)

    return SubmissionDM.build_from_data(get_resource_content(submission_url))


def build_create_submission_payload(submission, data):
    return {
        'message': 'Creating submission %s' % submission,
        'content': base64.b64encode(dump_json(data))
    }


def build_modify_submission_payload(submission, data, sha):
    return {
        'message': 'Updating submission %s' % submission,
        'sha': sha,
        'content': base64.b64encode(dump_json(data))
    }


def dump_json(data):
    return ENCODER.encode(data)


@statsd.timed('cabinet.put.submission')
def build_submission(submission, shell_submission_dm):
    """
    Used to build a shell submission file in the cabinet
    Throws CabinetSubmissionMultipleCreateException if trying to create submission which already exists
    """

    # submission is indirectly used to save the order of the questions and the order of the options
    # (basically the containers with their subparts fully dealt and shuffled)

    submission_url = build_submission_data_url(submission)

    if submission_exists(submission):
        raise CabinetSubmissionExistsException("Submission file exists for resource at: %s" % submission_url)

    # TODO: possible race condition here

    if CABINET_DEBUG:
        json_dict = build_create_submission_payload(submission, shell_submission_dm)
        github_cabinet_put(submission_url, json_dict)

    else:
        nginx_cabinet_put(submission_url, dump_json(shell_submission_dm), build_config_filename(submission.pk))


def github_cabinet_put(url, json_dict):
    requests.put(url, headers=HEADERS, json=json_dict)


def nginx_cabinet_put(url, json_str, filename):
    files = {
        'file': (filename, json_str)
    }
    requests.put(url, headers=HEADERS, files=files)


@statsd.timed('cabinet.update.submission')
def update_submission(submission, submission_dm):
    submission_url = build_submission_data_url(submission)

    if not submission_exists(submission):
        raise CabinetSubmissionMissingException("Submission file missing for resource at: %s" % submission_url)

    if CABINET_DEBUG:
        sha = get_resource_sha(submission_url)
        json_dict = build_modify_submission_payload(submission, submission_dm, sha)
        github_cabinet_put(submission_url, json_dict)

    else:
        nginx_cabinet_put(submission_url, dump_json(submission_dm), build_config_filename(submission.pk))


def submission_exists(submission):
    submission_url = build_submission_data_url(submission)
    return get_resource_exists(submission_url)


def get_question_img_url(question, question_data_type, img_filename):
    return os.path.join(build_question_url_stub(question, question_data_type), 'img', img_filename)


def get_question_img_url_secure(user, question, question_data_type, img_filename):
    img_url = get_question_img_url(question, question_data_type, img_filename)
    raw_secure_url = user.username + ENCODING_SEPERATOR + img_url
    signed_secure_url = SIGNER.sign(raw_secure_url)
    return os.path.join(SECURE_STATIC_URL, urlsafe_base64_encode(signed_secure_url))


@statsd.timed('cabinet.get.assignment')
def build_assignment(user, assignment_questions_list):
    question_dms = []
    # TODO: verify that the ordering of questions returned by this manytomanyfield lookup is consistent
    for question_db in assignment_questions_list.questions.all():
        question_dm = get_question(question_db)
        question_dm.build_img_urls(user)
        question_dms.append(question_dm)

    return question_dms


def extract_school_id_from_resource_url(resource_url):
    if CABINET_DEBUG:
        school_id_part_index = 10
    else:
        school_id_part_index = 6
    return resource_url.split('/')[school_id_part_index]




