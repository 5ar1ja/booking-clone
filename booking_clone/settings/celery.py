# Python modules
import os

# Third-party modules
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.dev')

app = Celery('booking_clone')

# Using a string here means the worker doesn't have to serializee the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self) -> None:
    print(f'Request: {self.request!r}')
