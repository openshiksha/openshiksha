class InvalidStateError(Exception):
    pass

class InvalidOpenShikshaError(InvalidStateError):
    def __init__(self, label, value, *args, **kwargs):
        super(InvalidOpenShikshaError, self).__init__("Invalid OpenShiksha %s: %s" % (label, value))


class InvalidOpenShikshaTypeError(InvalidOpenShikshaError):
    def __init__(self, label, value, *args, **kwargs):
        super(InvalidOpenShikshaTypeError, self).__init__(label + ' type', value)


class InvalidOpenShikshaGroupError(InvalidOpenShikshaError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaGroupError, self).__init__('group', value)


class InvalidOpenShikshaEnvError(InvalidOpenShikshaError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaEnvError, self).__init__('environ', value)

class InvalidOpenShikshaAssignmentTypeError(InvalidOpenShikshaTypeError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaAssignmentTypeError, self).__init__('assignment', value)

class InvalidContentTypeError(InvalidOpenShikshaTypeError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidContentTypeError, self).__init__('content', value)

class InvalidOpenShikshaQuestionTypeError(InvalidOpenShikshaTypeError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaQuestionTypeError, self).__init__('question', value)


class InvalidOpenShikshaOptionTypeError(InvalidOpenShikshaTypeError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaOptionTypeError, self).__init__('option', value)


class InvalidOpenShikshaContentTypeError(InvalidOpenShikshaTypeError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaContentTypeError, self).__init__('content', value)

class InvalidOpenShikshaConditionalAnswerFormatError(InvalidOpenShikshaError):
    def __init__(self, value, *args, **kwargs):
        super(InvalidOpenShikshaConditionalAnswerFormatError, self).__init__('conditional answer format', value)


class NoneArgumentError(Exception):
    def __init__(self, argument, *args, **kwargs):
        super(NoneArgumentError, self).__init__("Unexpected None argument: %s" % argument)


# TODO: better error messages
class EvalSanitizationError(Exception):
    pass


class TagMismatchError(Exception):
    pass

class UncorrectedSubmissionError(InvalidStateError):
    def __init__(self, *args, **kwargs):
        super(UncorrectedSubmissionError, self).__init__("Tried to render uncorrected submission as corrected")


class SubmissionFormError(InvalidStateError):
    pass