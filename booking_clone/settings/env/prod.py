# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = []  # Add production domains here, e.g. ["yourdomain.com", "www.yourdomain.com"]
INTERNAL_IPS = []  # No debug toolbar in production


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
}
