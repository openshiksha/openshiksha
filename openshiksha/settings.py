# Django settings for openshiksha project.

import os
import sys

from django.core.urlresolvers import reverse

from core.routing.urlnames import UrlNames
from core.utils.constants import OpenShikshaEnv
from openshiksha.exceptions import InvalidOpenShikshaEnvError

CONTACT_PHONE = os.getenv('OPENSHIKSHA_CONTACT_PHONE')
SALES_PHONE = os.getenv('OPENSHIKSHA_SALES_PHONE')
CONTACT_EMAIL = 'contact@openshiksha.org'

OVERVIEW_VIDEO_PK = 1

# set environ and debug values
if os.getenv('OPENSHIKSHA_ENV') == 'PROD':
    ENVIRON = OpenShikshaEnv.PROD
    DEBUG = False

# check if running on qa
elif os.getenv('OPENSHIKSHA_ENV') == 'QA':
    ENVIRON = OpenShikshaEnv.QA
    DEBUG = False

else:
    ENVIRON = OpenShikshaEnv.LOCAL
    DEBUG = True

SLEEP_MODE = bool(os.getenv('OPENSHIKSHA_SLEEP_MODE'))
# uncomment the line below to test SLEEP mode locally
# SLEEP_MODE = True

PASSWORD_RESET_TIMEOUT_DAYS = 7

SETTINGS_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SETTINGS_ROOT)

LOCAL_SECRET_KEY = '!x5@#nf^s53jwqx)l%na@=*!(1x+=jr496_yq!%ekh@u0pp1+n'
MAILGUN_SANDBOX_USER = 'postmaster@sandboxab360baee25e495dbb8dd423eab0e2fb.mailgun.org'
MAILGUN_SANDBOX_FROM_EMAIL = 'OpenShiksha Sandbox <%s>' % MAILGUN_SANDBOX_USER
MAILGUN_HOST = 'smtp.mailgun.org'

DB_NAME = 'openshiksha'
DB_USER = 'openshiksha_app'

if ENVIRON == OpenShikshaEnv.PROD:
    SECRET_KEY = os.getenv('OPENSHIKSHA_SECRET_KEY')
    EMAIL_HOST_USER = 'postmaster@openshiksha.org'
    DEFAULT_FROM_EMAIL = 'OpenShiksha <%s>' % EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = os.getenv('OPENSHIKSHA_EMAIL_HOST_PASSWORD')

    
    DB_PASSWORD = os.getenv('OPENSHIKSHA_DB_PASSWORD')
    DB_HOST = os.getenv('OPENSHIKSHA_DB_HOST')
    DB_PORT = os.getenv('OPENSHIKSHA_DB_PORT')

elif ENVIRON == OpenShikshaEnv.QA:
    SECRET_KEY = os.getenv('OPENSHIKSHA_SECRET_KEY')
    EMAIL_HOST_USER = MAILGUN_SANDBOX_USER
    DEFAULT_FROM_EMAIL = MAILGUN_SANDBOX_FROM_EMAIL
    EMAIL_HOST_PASSWORD = os.getenv('OPENSHIKSHA_EMAIL_HOST_PASSWORD')

    DB_PASSWORD = os.getenv('OPENSHIKSHA_DB_PASSWORD')
    DB_HOST = os.getenv('OPENSHIKSHA_DB_HOST')
    DB_PORT = os.getenv('OPENSHIKSHA_DB_PORT')

elif ENVIRON == OpenShikshaEnv.LOCAL:
    SECRET_KEY = LOCAL_SECRET_KEY
    EMAIL_HOST_USER = MAILGUN_SANDBOX_USER
    DEFAULT_FROM_EMAIL = MAILGUN_SANDBOX_FROM_EMAIL
    EMAIL_HOST_PASSWORD = os.getenv('OPENSHIKSHA_EMAIL_HOST_PASSWORD')

    DB_PASSWORD = 'Soc1alsev@'
    DB_HOST = ''
    DB_PORT = ''

else:
    raise InvalidOpenShikshaEnvError(ENVIRON)

ADMINS = (
    ('OpenShiksha Exception', 'exception@openshiksha.org'),
)
MANAGERS = (
    ('OpenShiksha Contact', CONTACT_EMAIL),
)

EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_TIMEOUT = 20  # seconds
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_HOST = MAILGUN_HOST

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

INTERNAL_IPS = ()  # this should be automatically set by debug_toolbar to include localhost

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Kolkata'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            # Project-specific location of template files
            os.path.join(SETTINGS_ROOT, 'templates'),
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'openshiksha.context_processors.settings',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MAX_CHARFIELD_LENGTH = 255  # Applying this limit to allow safely marking any CharField as unique. For longer requirement use TextField

# Project-specific location of fixture files
FIXTURE_DIRS = (
    os.path.join(SETTINGS_ROOT, 'fixtures'),
)

MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'openshiksha.wsgi.application'

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

    # Now OpenShiksha-specific apps
    'core',
    'cabinet',
    'croupier',
    'grader',
    'concierge',
    'sphinx',
    'edge',
    'ink',
    'focus',
    'pylon',
    'lodge',
    'challenge'
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
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'log_file': {
            'level': 'DEBUG',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'devops', 'django.log'),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['log_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}
# Inbuilt Login Configuration
LOGIN_URL = UrlNames.LOGIN.name
LOGIN_REDIRECT_URL = UrlNames.HOME.name  # this is where user is redirected if login view gets no 'next' param

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
if ENVIRON == OpenShikshaEnv.PROD:
    ALLOWED_HOSTS = [
        '.openshiksha.org',  # Allow FQDN, domain and subdomains
    ]
    SITE_ID = 1  # prod site
elif ENVIRON == OpenShikshaEnv.QA:
    ALLOWED_HOSTS = [
        '.openshiksha-qa.org',  # Allow FQDN, domain and subdomains 
    ]
    SITE_ID = 3  # qa site
elif ENVIRON == OpenShikshaEnv.LOCAL:
    ALLOWED_HOSTS = []
    SITE_ID = 2  # localhost site
else:
    raise InvalidOpenShikshaEnvError(ENVIRON)


if SLEEP_MODE:
    ROOT_URLCONF = 'openshiksha.urls.sleep_mode'
else:
    if ENVIRON == OpenShikshaEnv.PROD:
        ROOT_URLCONF = 'openshiksha.urls.prod'
    elif ENVIRON == OpenShikshaEnv.QA:
        ROOT_URLCONF = 'openshiksha.urls.local'  # qa just uses local urls for now
    elif ENVIRON == OpenShikshaEnv.LOCAL:
        ROOT_URLCONF = 'openshiksha.urls.local'
    else:
        raise InvalidOpenShikshaEnvError(ENVIRON)
