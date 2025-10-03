import os
from pathlib import Path
from celery import Celery
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theater_service.settings.base")

app = Celery("theater_service")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.broker_use_ssl = False
app.conf.redis_backend_use_ssl = False
app.conf.broker_connection_retry_on_startup = True

from django.conf import settings


def _get(name: str, default=None):
    return getattr(settings, name, None) or os.getenv(name) or default


def _normalize_redis_url(url: str | None) -> str | None:
    if not url:
        return url
    u = url.strip()
    if u.startswith("rediss://"):
        return "redis://" + u[len("rediss://"):]
    return u


broker_url = _get("CELERY_BROKER_URL") or os.getenv("SalaryBrokerUrl")
result_backend = _get("CELERY_RESULT_BACKEND") or os.getenv("SalaryResultBackend") or broker_url

broker_url = _normalize_redis_url(broker_url)
result_backend = _normalize_redis_url(result_backend)

if broker_url:
    app.conf.broker_url = broker_url
if result_backend:
    app.conf.result_backend = result_backend

app.autodiscover_tasks()
