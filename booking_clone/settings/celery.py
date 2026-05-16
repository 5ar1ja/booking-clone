# Python modules
import os

# Third-party modules
from celery import Celery

# Project modules
from settings.conf import ALLOWED_ENV_IDS, ENV_ID


assert ENV_ID in ALLOWED_ENV_IDS, f"Invalid ENV_ID: {ENV_ID}. Allowed values are: {ALLOWED_ENV_IDS}"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')

app = Celery('booking_clone')

# Using a string here means the worker doesn't have to serialize the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self) -> None:
    print(f'Request: {self.request!r}')
