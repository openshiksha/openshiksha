"""
Cabinet app configuration
"""

from django.apps import AppConfig


class CabinetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "openshiksha.apps.cabinet"
    verbose_name = "Cabinet Integration"
