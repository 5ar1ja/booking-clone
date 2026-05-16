# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = []  # Add production domains here, e.g. ["yourdomain.com", "www.yourdomain.com"]
INTERNAL_IPS = [
    "127.0.0.1",
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'booking_clone'),
    }
}
