import os

from core.routing.urlnames import match_all_nested_index_url_matcher
from sphinx.urlnames import AppUrlName


class FrontendUrlName(AppUrlName):
    APP_NAME = 'app'

    def __init__(self, name):
        super(FrontendUrlName, self).__init__(FrontendUrlName.APP_NAME, name)


class FrontendIndexUrlName(FrontendUrlName):  # custom case
    def __init__(self):
        super(FrontendIndexUrlName, self).__init__('index')
        self.url_matcher = match_all_nested_index_url_matcher(self.url_matcher)


class FrontendUrlNames(object):
    INDEX = FrontendIndexUrlName()
