import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theater_service.settings.base")
app = Celery("theater_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
