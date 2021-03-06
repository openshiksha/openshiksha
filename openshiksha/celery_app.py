import os

from celery import Celery
from django.core.management import call_command

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openshiksha.settings')

celery_app = Celery('openshiksha')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
celery_app.autodiscover_tasks()


# Register project-level tasks here (app-level tasks go into tasks.py inside the app)
@celery_app.task(bind=True)
def debug_task(self, arg):
    print 'Request: ' + repr(self.request)
    return arg

@celery_app.task
def clearsessions():
    call_command('clearsessions')
