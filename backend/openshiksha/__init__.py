"""
OpenShiksha Modern Platform

Django 4.2 + Django REST Framework backend
"""

__version__ = '2.0.0-dev'

# Load Celery app
from .celery import app as celery_app

__all__ = ('celery_app',)
