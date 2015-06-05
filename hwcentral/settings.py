# Django settings for hwcentral project.

import os

from core.routing.urlnames import UrlNames


DEBUG = True
TEMPLATE_DEBUG = DEBUG

SETTINGS_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SETTINGS_ROOT)
ASSIGNMENTS_ROOT = os.path.join(PROJECT_ROOT, 'core', 'assignments')
SUBMISSIONS_ROOT = os.path.join(PROJECT_ROOT, 'core', 'submissions')
QUESTIONS_ROOT = os.path.join(PROJECT_ROOT, 'core', 'questions')

ADMINS = (
    ('Oasis Vali', 'oasis.vali@gmail.com'),
)

# Make this unique, and don't share it with anybody
SECRET_KEY = '!x5@#nf^s53jwqx)l%na@=*!(1x+=jr496_yq!%ekh@u0pp1+n'

MANAGERS = ADMINS

if DEBUG:
    DB_NAME = 'hwcentral-dev'

else:
    DB_NAME = 'hwcentral-qa'

DB_USER = 'root'
DB_PASSWORD = 'hwcentral'
# signifies localhost
DB_HOST = ''
DB_PORT = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,

        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,

        'OPTIONS': {
            'init_command': 'SET character_set_connection=utf8,collation_connection=utf8_unicode_ci'
        },
    },
}

# Django debug toolbar config
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}
INTERNAL_IPS = ('127.0.0.1',)

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static_root')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    # The following loader will pull in sttic content from dirs specified in STATICFILES_DIRS
    'django.contrib.staticfiles.finders.FileSystemFinder',
    # The following loader will pull in static content from a 'static/' folder in each installed app
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Project-specific location of static files
STATICFILES_DIRS = (
    os.path.join(SETTINGS_ROOT, 'static'),
)

# Project-specific location of static files
TEMPLATE_DIRS = (
    os.path.join(SETTINGS_ROOT, 'templates'),
)

# Project-specific location of fixture files
FIXTURE_DIRS = (
    os.path.join(SETTINGS_ROOT, 'fixtures'),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    # The following loader will pull in templates from dirs specified in TEMPLATE_DIRS
    'django.template.loaders.filesystem.Loader',
    # The following loader will pull in templates from a 'templates/' folder in each installed app
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'hwcentral.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'hwcentral.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'debug_toolbar',
    'django_extensions',
    'south',

    # Now HWCentral-specific apps
    'core',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Inbuilt Login Configuration
LOGIN_URL = UrlNames.LOGIN.name
LOGIN_REDIRECT_URL = UrlNames.HOME.name