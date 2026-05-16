import os
import dj_database_url

# Project modules
from settings.base import *  # noqa: F403


DEBUG = False
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]

# Required in production so Django's CSRF middleware accepts requests
# from the deployed domain. Set CSRF_TRUSTED_ORIGINS in Render env vars,
# e.g. https://your-app.onrender.com (Render also sets RENDER_EXTERNAL_URL automatically).
_render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
_extra_origins = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]
CSRF_TRUSTED_ORIGINS = ([_render_url] if _render_url else []) + _extra_origins

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