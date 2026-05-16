# Python modules
import os

# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = []  # Add production domains here, e.g. ["somedomain.com", "www.somedomain.com"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(BASE_DIR), 'data', 'db.sqlite3'),  # noqa: F405
    }
}
