# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
INTERNAL_IPS = []  # No debug toolbar in production


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/app/data/db.sqlite3',
    },
}
