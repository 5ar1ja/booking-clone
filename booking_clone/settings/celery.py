import os

from celery import Celery
from settings.conf import ALLOWED_ENV_IDS, ENV_ID

assert ENV_ID in ALLOWED_ENV_IDS, f"Invalid ENV_ID: {ENV_ID}. Allowed values are: {ALLOWED_ENV_IDS}"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')

app = Celery('booking_clone')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
