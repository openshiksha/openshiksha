import json

from django.shortcuts import render
from django.utils.safestring import mark_safe


from core.data_models.question import build_question_subpart_from_data
from core.models import QuestionTag, Subject, Chapter
from core.utils.references import EdgeSpecialTags
from core.utils.json import OpenShikshaJsonResponse
from croupier.constraints import SubpartVariableConstraints
from croupier.croupier_api import deal_subpart
from sphinx.urlnames import SphinxUrlNames


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
    for subpart_data in question_data.subparts:
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
