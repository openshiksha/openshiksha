from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, HttpResponseNotFound

from openshiksha import settings


class OpenShikshaJsonResponse(JsonResponse):
    def __init__(self, response_object):
        super(OpenShikshaJsonResponse, self).__init__(response_object, encoder=OpenShikshaJSONEncoder, safe=False)


class OpenShikshaJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, JSONModel):
            return o.get_json()
        if isinstance(o, Decimal):
            return str(o)
        return super(OpenShikshaJSONEncoder, self).default(o)


ENCODER = OpenShikshaJSONEncoder(indent=2)


def dump_json_string(data):
    return ENCODER.encode(data)

class JSONModel(object):
    def get_json(self):
        return self.__dict__

class Json404Response(JsonResponse, HttpResponseNotFound):
    message = "Resource Not Found"

    def __init__(self, exception=None):
        if exception is not None and settings.DEBUG:
            self.message = str(exception)
        super(Json404Response, self).__init__({"message": self.message})
