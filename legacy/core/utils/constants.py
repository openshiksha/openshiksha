VIEWMODEL_KEY = 'vm'


class OpenShikshaRegex(object):
    NUMERIC = r'\d+'
    BASE64 = r'[\w\-]+'


class HttpMethod(object):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


class OpenShikshaQuestionType(object):
    MCSA = 1
    MCMA = 2
    NUMERIC = 3
    TEXTUAL = 4
    CONDITIONAL = 5


class OpenShikshaAssignmentType(object):
    INACTIVE = 'inactive'
    UNCORRECTED = 'uncorrected'
    CORRECTED = 'corrected'
    STUDENT = 'student'


class OpenShikshaStudentAssignmentSubmissionType(object):
    UNCORRECTED = 'student'  # type is used for directing to the correct template, and uncorrected student assignments use student.html
    CORRECTED = 'corrected'

class OpenShikshaQuestionDataType(object):
    CONTAINER = 'containers'
    SUBPART = 'raw'


class OpenShikshaConditionalAnswerFormat(object):
    TEXTUAL = 1
    NUMERIC = 2


class OpenShikshaEnv(object):
    PROD = 1
    QA = 3
    LOCAL = 4
