import os
import dj_database_url

# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",") + ["*"]

INTERNAL_IPS = [
    "127.0.0.1",
]

# Insert WhiteNoiseMiddleware after SecurityMiddleware
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
    )
}