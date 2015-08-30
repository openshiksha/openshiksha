###
#
# This file contains all the submission-related viewmodels used in the core hwcentral templates. for datamodels which
# are used by the logic, look at the data_models module
#
###
from core.forms.submission import ReadOnlySubmissionFormCorrected
from core.routing.urlnames import UrlNames
from core.utils.constants import HWCentralQuestionDataType, HWCentralQuestionType, HWCentralConditionalAnswerFormat
from core.utils.labels import get_fraction_label, get_subjectroom_label, get_datetime_label
from core.view_models.base import FormBody, ReadOnlyFormBody


class BaseSubmissionIdBody(object):
    """
    sets up all the meta data (info-objects) associated with the submission - use like mixin (see below)
    """

    def __init__(self, submission_db):
        self.submission_info = SubmissionInfo(submission_db)
        self.assignment_info = AssignmentInfo(submission_db.assignment)
        self.aql_info = AQLInfo(submission_db.assignment.assignmentQuestionsList)


class CorrectedSubmissionIdBody(ReadOnlyFormBody, BaseSubmissionIdBody):
    def __init__(self, submission_db, submission_vm):
        BaseSubmissionIdBody.__init__(self, submission_db)  # non-super call to avoid messy resolution
        self.submission_marks = get_fraction_label(submission_db.marks)
        # build a readonly form representation of the submission so it is easier to render
        readonly_form = ReadOnlySubmissionFormCorrected(submission_vm)
        super(CorrectedSubmissionIdBody, self).__init__(readonly_form)


class CorrectedSubmissionIdBodySubmissionUser(CorrectedSubmissionIdBody):
    pass


class CorrectedSubmissionIdBodyDifferentUser(CorrectedSubmissionIdBody):
    def __init__(self, submission_db, submission_vm, user):
        # customize submission viewmodel for the given user
        submission_vm.change_img_urls_for_user(user)
        super(CorrectedSubmissionIdBodyDifferentUser, self).__init__(submission_db, submission_vm)


class UncorrectedSubmissionIdBody(FormBody, BaseSubmissionIdBody):
    def __init__(self, submission_form, submission_db):
        BaseSubmissionIdBody.__init__(self, submission_db)  #non-super call to avoid messy resolution
        self.submission_id = submission_db.pk
        super(UncorrectedSubmissionIdBody, self).__init__(submission_form, UrlNames.SUBMISSION_ID.name)


class SubmissionInfo(object):
    def __init__(self, submission):
        self.completion = get_fraction_label(submission.completion)
        self.timestamp = get_datetime_label(submission.timestamp)


class AQLInfo(object):
    def __init__(self, assignment_questions_list):
        self.title = "%s - %i" % (assignment_questions_list.get_topic(), assignment_questions_list.number)
        self.description = assignment_questions_list.description


class AssignmentInfo(object):
    """
    Contains all the information regarding the submission's assignment
    """

    def __init__(self, assignment):
        self.subjectroom = get_subjectroom_label(assignment.subjectRoom)
        self.due = get_datetime_label(assignment.due)


class SubmissionVMBase(object):
    def __init__(self, answers):
        self.answers = answers


class SubmissionVMUnprotected(SubmissionVMBase):
    """
    This is basically just the submission dm, with added functionality to update the image urls for a given user
    """

    def __init__(self, submission_dm):
        super(SubmissionVMUnprotected, self).__init__(submission_dm.answers)
        self.questions = submission_dm.questions

    # NOTE: only the non-protected version of submissionVM should need to change img urls for user
    def change_img_urls_for_user(self, user):
        for question in self.questions:
            # change by overwriting
            question.build_img_urls(user)


class SubmissionVMProtected(SubmissionVMBase):
    def __init__(self, submission_dm):
        super(SubmissionVMProtected, self).__init__(submission_dm.answers)
        self.questions = submission_dm.get_protected_questions()


class QuestionPartProtected(object):
    TYPES = HWCentralQuestionType  # associating enum with this dm so that it is available in templates

    def __init__(self, question_part_dm):
        self.type = question_part_dm.type
        self.content = question_part_dm.content
        self.subpart_index = question_part_dm.subpart_index

        self.hint = question_part_dm.hint

    def build_img_urls(self, user, question):
        self.content.build_img_url(user, question, HWCentralQuestionDataType.SUBPART)
        if self.hint is not None:
            self.hint.build_img_url(user, question, HWCentralQuestionDataType.SUBPART)


class MCOptionsProtected(object):
    def __init__(self, mc_options_dm):
        self.combined = mc_options_dm.get_combined_options()
        self.order = mc_options_dm.order

    def build_img_urls(self, user, question):
        for option in self.combined:
            option.build_img_url(user, question, HWCentralQuestionDataType.SUBPART)


class MCSAOptionsProtected(MCOptionsProtected):
    def __init__(self, mcsa_options_dm):
        super(MCSAOptionsProtected, self).__init__(mcsa_options_dm)
        self.use_dropdown_widget = mcsa_options_dm.use_dropdown_widget


class MCMAOptionsProtected(MCOptionsProtected):
    pass


class MCQuestionPartProtected(QuestionPartProtected):
    def build_img_urls(self, user, question):
        super(MCQuestionPartProtected, self).build_img_urls(user, question)
        self.options.build_img_urls(user, question)


class MCSAQuestionPartProtected(MCQuestionPartProtected):
    def __init__(self, mcsa_question_part_dm):
        super(MCSAQuestionPartProtected, self).__init__(mcsa_question_part_dm)
        self.options = MCSAOptionsProtected(mcsa_question_part_dm.options)


class MCMAQuestionPartProtected(MCQuestionPartProtected):
    def __init__(self, mcma_question_part_dm):
        super(MCMAQuestionPartProtected, self).__init__(mcma_question_part_dm)
        self.options = MCMAOptionsProtected(mcma_question_part_dm.options)


class NumericQuestionPartProtected(QuestionPartProtected):
    pass


class TextualQuestionPartProtected(QuestionPartProtected):
    def __init__(self, textual_question_part_dm):
        super(TextualQuestionPartProtected, self).__init__(textual_question_part_dm)
        self.show_toolbox = textual_question_part_dm.show_toolbox


class ConditionalTargetProtected(object):
    FORMATS = HWCentralConditionalAnswerFormat  # associating enum with this dm so that it is available in templates

    def __init__(self, conditional_target_dm):
        self.num_answers = conditional_target_dm.num_answers
        self.answer_format = conditional_target_dm.answer_format
        if self.answer_format == ConditionalTargetProtected.FORMATS.TEXTUAL:
            self.show_toolbox = conditional_target_dm.show_toolbox


class ConditionalQuestionPartProtected(QuestionPartProtected):
    def __init__(self, conditional_question_part_dm):
        super(ConditionalQuestionPartProtected, self).__init__(conditional_question_part_dm)
        self.answer = ConditionalTargetProtected(conditional_question_part_dm.answer)
