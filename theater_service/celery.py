import os
from celery import Celery
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theater_service.settings.base")
app = Celery("theater_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
