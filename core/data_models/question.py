from django.utils.safestring import mark_safe

from core.data_models.answer import MCSAQAnswer, MCMAQAnswer, TextualAnswer, NumericAnswer, ConditionalAnswer
from core.data_models.aql import add_img_reloader
from core.models import Question
from core.utils.constants import OpenShikshaQuestionDataType, OpenShikshaQuestionType, OpenShikshaConditionalAnswerFormat
from core.utils.json import JSONModel
from core.utils.regex import evaluate_substitute, substitute_img
from core.view_models.submission_id import MCSAQuestionPartProtected, MCMAQuestionPartProtected, \
    TextualQuestionPartProtected, NumericQuestionPartProtected, ConditionalQuestionPartProtected
from openshiksha.exceptions import InvalidOpenShikshaQuestionTypeError


def no_tex(text):
    TEX_MARKERS = ['\\[', '\\]', '\\(', '\\)']
    return not any(tex_marker in text for tex_marker in TEX_MARKERS)


class QuestionElem(JSONModel):
    """
    Wrapper around the building block of a question. text + image (at least one must exist)
    """

    @classmethod
    def from_data(cls, data):
        if data is None:
            return None

        assert ( ('text' in data) or ('img' in data) )
        return cls(data.get('text'), data.get('img'), data.get('img_url'))

    def __init__(self, text, img, img_url):
        self.text = None if text is None else mark_safe(text)
        self.img = img
        self.img_url = img_url

    def build_img_url(self, user, question, question_data_type):
        """
        This is done as a seperate step and not during initialization so that the QuestionElem creation is not dependant
        on extra contextual data such as user that the cabinet needs to build the secure url
        """
        if self.img is not None:
            from cabinet import cabinet_api
            self.img_url = cabinet_api.get_question_img_url_secure(user, question, question_data_type, self.img)
        else:
            self.img_url = None

        if self.text is not None:
            self.text = mark_safe(add_img_reloader(substitute_img(self.text, user, question, question_data_type)))

    def is_plaintext(self):
        """
        Checks whether this QuestionElem contains plain text ONLY (no tex or img)
        """
        return (self.img is None) and no_tex(self.text)

    def evaluate_substitute(self, variable_values):
        if self.text is not None:
            self.text = mark_safe(evaluate_substitute(self.text, variable_values))


def build_question_subpart_from_data(subpart_data):
    """
    Checks the provided data object (dictionary) for the type of the subpart and builds a Python object of the right type
    """
    subpart_type = subpart_data['type']

    if subpart_type == OpenShikshaQuestionType.MCSA:
        question_part = MCSAQuestionPart(subpart_data)
    elif subpart_type == OpenShikshaQuestionType.MCMA:
        question_part = MCMAQuestionPart(subpart_data)
    elif subpart_type == OpenShikshaQuestionType.NUMERIC:
        question_part = NumericQuestionPart(subpart_data)
    elif subpart_type == OpenShikshaQuestionType.TEXTUAL:
        question_part = TextualQuestionPart(subpart_data)
    elif subpart_type == OpenShikshaQuestionType.CONDITIONAL:
        question_part = ConditionalQuestionPart(subpart_data)
    else:
        raise InvalidOpenShikshaQuestionTypeError(subpart_type)

    return question_part


class QuestionDM(JSONModel):
    """
    Overall wrapper on cabinet question data
    """

    @classmethod
    def from_data(cls, data):
        subparts = []
        for subpart_data in data['subparts']:
            subparts.append(build_question_subpart_from_data(subpart_data))

        return cls(data['pk'], QuestionContainer(data['container']), subparts)

    def __init__(self, pk, container, subparts):
        self.pk = pk
        self.container = container
        self.subparts = subparts

    def build_img_urls(self, user):
        question = Question.objects.get(pk=self.pk)
        self.container.build_img_urls(user, question)
        for subpart in self.subparts:
            subpart.build_img_urls(user, question)

    def get_protected_subparts(self):
        return [subpart.get_protected() for subpart in self.subparts]

class QuestionContainer(JSONModel):
    """
    Wrapper around the data that resides in a question container file
    """

    def __init__(self, data):
        self.hint = QuestionElem.from_data(data.get("hint"))
        self.content = QuestionElem.from_data(data.get("content"))

        self.subparts = data['subparts']

    def build_img_urls(self, user, question):
        if self.hint is not None:
            self.hint.build_img_url(user, question, OpenShikshaQuestionDataType.CONTAINER)
        if self.content is not None:
            self.content.build_img_url(user, question, OpenShikshaQuestionDataType.CONTAINER)

class QuestionPart(JSONModel):
    """
    Wrapper around the data that resides in a raw question file
    """

    TYPES = OpenShikshaQuestionType  # associating enum with this dm so that it is available in templates
    ANSWER_MODEL = None  # to be set by child classes

    def __init__(self, data):
        self.type = data['type']
        self.content = QuestionElem.from_data(data['content'])
        self.subpart_index = data['subpart_index']

        self.hint = QuestionElem.from_data(data.get("hint"))
        self.solution = QuestionElem.from_data(data.get("solution"))

    def build_img_urls(self, user, question):
        self.content.build_img_url(user, question, OpenShikshaQuestionDataType.SUBPART)
        if self.hint is not None:
            self.hint.build_img_url(user, question, OpenShikshaQuestionDataType.SUBPART)
        if self.solution is not None:
            self.solution.build_img_url(user, question, OpenShikshaQuestionDataType.SUBPART)

    def get_protected(self):
        raise NotImplementedError("subclass of QuestionPart must implement method get_protected")

    def evaluate_substitute(self, variable_values):
        self.content.evaluate_substitute(variable_values)
        if self.solution is not None:
            self.solution.evaluate_substitute(variable_values)

    def get_shell_answer(self):
        return self.ANSWER_MODEL.build_shell()

class MCOptions(JSONModel):
    """
    This is an abstract class
    """
    def __init__(self, data):
        self.incorrect = [QuestionElem.from_data(option) for option in data['incorrect']]
        assert len(self.incorrect) > 0
        self.order = data.get('order', None)

    def get_option_count(self):
        return len(self.incorrect)

    def build_img_urls(self, user, question):
        for option in self.incorrect:
            option.build_img_url(user, question, OpenShikshaQuestionDataType.SUBPART)

    def evaluate_substitute(self, variable_values):
        for option in self.incorrect:
            option.evaluate_substitute(variable_values)


class MCSAOptions(MCOptions):
    def __init__(self, data):
        super(MCSAOptions, self).__init__(data)
        self.correct = QuestionElem.from_data(data['correct'])
        self.use_dropdown_widget = data.get('use_dropdown_widget', False)  # disable by default
        if self.use_dropdown_widget:
            assert self.all_options_plaintext()

    def build_img_urls(self, user, question):
        super(MCSAOptions, self).build_img_urls(user, question)
        self.correct.build_img_url(user, question, OpenShikshaQuestionDataType.SUBPART)

    def evaluate_substitute(self, variable_values):
        super(MCSAOptions, self).evaluate_substitute(variable_values)
        self.correct.evaluate_substitute(variable_values)

    def get_option_count(self):
        # NOTE: correct option before incorrect
        return 1 + super(MCSAOptions, self).get_option_count()

    def get_combined_options(self):
        return [self.correct] + self.incorrect

    def all_options_plaintext(self):
        """
        Checks whether all the option QuestionElems for this Options object are text-only (no tex no img)
        @return: boolean result of check
        """
        for option in self.incorrect:
            if not option.is_plaintext():
                return False

        return self.correct.is_plaintext()

class MCMAOptions(MCOptions):
    def __init__(self, data):
        super(MCMAOptions, self).__init__(data)
        self.correct = [QuestionElem.from_data(option) for option in data['correct']]
        assert len(self.correct) > 0

    def get_combined_options(self):
        return self.correct + self.incorrect

    def get_option_count(self):
        # NOTE: correct option before incorrect
        return len(self.correct) + super(MCMAOptions, self).get_option_count()

    def build_img_urls(self, user, question):
        super(MCMAOptions, self).build_img_urls(user, question)
        for option in self.correct:
            option.build_img_url(user, question, OpenShikshaQuestionDataType.SUBPART)

    def evaluate_substitute(self, variable_values):
        super(MCMAOptions, self).evaluate_substitute(variable_values)
        for option in self.correct:
            option.evaluate_substitute(variable_values)


class MCQuestionPart(QuestionPart):
    def build_img_urls(self, user, question):
        super(MCQuestionPart, self).build_img_urls(user, question)
        self.options.build_img_urls(user, question)

    def evaluate_substitute(self, variable_values):
        super(MCQuestionPart, self).evaluate_substitute(variable_values)
        self.options.evaluate_substitute(variable_values)

class MCSAQuestionPart(MCQuestionPart):
    ANSWER_MODEL = MCSAQAnswer

    def __init__(self, data):
        super(MCSAQuestionPart, self).__init__(data)
        self.options = MCSAOptions(data['options'])

    def get_protected(self):
        return MCSAQuestionPartProtected(self)

class MCMAQuestionPart(MCQuestionPart):
    ANSWER_MODEL = MCMAQAnswer

    def __init__(self, data):
        super(MCMAQuestionPart, self).__init__(data)
        self.options = MCMAOptions(data['options'])

    def get_protected(self):
        return MCMAQuestionPartProtected(self)

class NumericTarget(JSONModel):
    def __init__(self, data):
        # casting to string to preserve precision in case of float when value is eventually cast to decimal
        self.value = str(data['value'])
        self.tolerance = data.get('tolerance')

        # IMPORTANT: always specify tolerance if answer value is a decimal

    def evaluate_substitute(self, variable_values):
        # casting to string to preserve precision in case of float when value is eventually cast to decimal
        self.value = str(evaluate_substitute(self.value, variable_values))
        # remove brakcets from value in case of negative answer value -- HACK (better way to have custom evaluation function for answer)
        self.value = self.value[1:-1] if (self.value.startswith('(') and self.value.endswith(')')) else self.value

class TextualQuestionPart(QuestionPart):
    ANSWER_MODEL = TextualAnswer

    def __init__(self, data):
        super(TextualQuestionPart, self).__init__(data)
        self.answer = data['answer']

    def get_protected(self):
        return TextualQuestionPartProtected(self)

    def evaluate_substitute(self, variable_values):
        super(TextualQuestionPart, self).evaluate_substitute(variable_values)
        self.answer = evaluate_substitute(self.answer, variable_values)

class NumericQuestionPart(QuestionPart):
    ANSWER_MODEL = NumericAnswer

    def __init__(self, data):
        super(NumericQuestionPart, self).__init__(data)
        self.unit = data.get("unit")
        if self.unit is not None:
            self.unit = mark_safe(self.unit)
        self.answer = NumericTarget(data['answer'])

    def get_protected(self):
        return NumericQuestionPartProtected(self)

    def evaluate_substitute(self, variable_values):
        super(NumericQuestionPart, self).evaluate_substitute(variable_values)
        self.answer.evaluate_substitute(variable_values)

class ConditionalTarget(JSONModel):
    FORMATS = OpenShikshaConditionalAnswerFormat  # associating enum with this dm so that it is available in templates

    def __init__(self, data):
        self.num_answers = data['num_answers']
        assert self.num_answers > 0
        self.condition = data['condition']
        self.answer_format = data['answer_format']

    def evaluate_substitute(self, variable_values):
        self.condition = evaluate_substitute(self.condition, variable_values)

class ConditionalQuestionPart(QuestionPart):
    ANSWER_MODEL = ConditionalAnswer

    def __init__(self, data):
        super(ConditionalQuestionPart, self).__init__(data)
        self.answer = ConditionalTarget(data['answer'])

    def get_protected(self):
        return ConditionalQuestionPartProtected(self)

    def evaluate_substitute(self, variable_values):
        super(ConditionalQuestionPart, self).evaluate_substitute(variable_values)
        self.answer.evaluate_substitute(variable_values)
