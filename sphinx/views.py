import json

from core.data_models.question import build_question_part_from_data
from core.utils.json import HWCentralJsonResponse
from croupier.croupier_api import deal_subpart
from croupier.data_models import SubpartVariableConstraints


def sphinx_failure_response(message):
    return HWCentralJsonResponse({
        'success': False,
        'message': message
    })


def sphinx_success_response(data):
    return HWCentralJsonResponse({
        'success': True,
        'payload': data
    })


def deal_subpart_post(request):
    request_data = json.loads(request.body)  # ajax post data has to be accessed here instead of request.POST

    if 'subpart' not in request_data:
        return sphinx_failure_response('No subpart data provided')

    subpart_data = request_data['subpart']

    try:
        subpart = build_question_part_from_data(subpart_data)
    except Exception, e:
        return sphinx_failure_response('Malformed subpart data: %s' % e)

    try:
        variable_constraints = SubpartVariableConstraints(subpart_data.get('variable_constraints'))
    except Exception, e:
        return sphinx_failure_response('Malformed variable constraints data: %s' % e)

    try:
        dealt_subpart = deal_subpart(subpart, variable_constraints)
    except Exception, e:
        return sphinx_failure_response('Dealing error: %s' % e)

    return sphinx_success_response(dealt_subpart)