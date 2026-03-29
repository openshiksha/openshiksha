"""
Edge app configuration
"""

from django.apps import AppConfig


class EdgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'openshiksha.apps.edge'
    verbose_name = 'Analytics & Proficiency'
