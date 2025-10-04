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


def _normalize(url: str) -> str:
    return url.replace("rediss://", "redis://") if url else url


broker = _normalize(broker)
backend = _normalize(backend)

app.conf.update(
    broker_url=broker,
    result_backend=backend,
    broker_connection_retry_on_startup=True,
    broker_use_ssl=None,
    redis_backend_use_ssl=None,
)

app.autodiscover_tasks()
