from django.urls import path

from .views import EnquireView

urlpatterns = [
    path("enquire/", EnquireView.as_view(), name="enquire"),
]
