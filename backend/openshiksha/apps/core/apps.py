"""
Core app configuration
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'openshiksha.apps.core'
    verbose_name = 'Core'

    def ready(self):
        """
        Import signals when app is ready
        """
        import openshiksha.apps.core.signals  # noqa: F401
