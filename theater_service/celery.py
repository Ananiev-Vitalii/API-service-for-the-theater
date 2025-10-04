import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theater_service.settings.base")
app = Celery("theater_service")
app.config_from_object("django.conf:settings", namespace="CELERY")

broker = os.getenv("CELERY_BROKER_URL") or "redis://127.0.0.1:6379/0"
backend = os.getenv("CELERY_RESULT_BACKEND") or broker

app.conf.update(
    broker_url=broker,
    result_backend=backend,
    broker_connection_retry_on_startup=True,
)

app.autodiscover_tasks()
