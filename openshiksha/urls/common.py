from django.conf.urls import url
from core.routing.routers import dynamic_router, REDIRECT_EXPLICIT_ARGS_KEY, redirect_router
from core.routing.urlnames import UrlNames
from core.utils.constants import HttpMethod
from challenge.urlnames import ChallengeUrlNames
from lodge.urlnames import LodgeUrlNames
from core.views import secure_static_get, test_500_get
from openshiksha.settings import OVERVIEW_VIDEO_PK
from lodge.views import index_get as lodge_index_get
from challenge.views import index_get as challenge_index_get

def get_all_mode_urlpatterns():
    return [
        UrlNames.INDEX.create_index_route(),

        # UrlNames.ABOUT.create_static_route(),

        # secure-static must still be available while sleeping otherwise grading (specifically, shell submission creation) fails
        # TODO: this is a hack, fix it, no reason for secure static to be exposed while sleeping
        url(UrlNames.SECURE_STATIC.url_matcher, dynamic_router, {HttpMethod.GET: secure_static_get},
            name=UrlNames.SECURE_STATIC.name),

        url(LodgeUrlNames.INDEX.url_matcher, dynamic_router, {HttpMethod.GET: lodge_index_get},
            name=LodgeUrlNames.INDEX.name),

        url(r'^overview/$', redirect_router,
            {'target_view_name': LodgeUrlNames.INDEX.name, REDIRECT_EXPLICIT_ARGS_KEY: [OVERVIEW_VIDEO_PK]},
            name='overview_video'),

        url(ChallengeUrlNames.INDEX.url_matcher, dynamic_router, {HttpMethod.GET: challenge_index_get},
            name=ChallengeUrlNames.INDEX.name),
        url(r'^challenge/$', dynamic_router, {HttpMethod.GET: challenge_index_get}),
        # add a error page view to test error page
        url('^tTrNJnEzCxJfqtDBtWO2cOo6dsA/', dynamic_router, {HttpMethod.GET: test_500_get}),
    ]
