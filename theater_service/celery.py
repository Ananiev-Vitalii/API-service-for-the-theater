import os
import logging
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

if broker.startswith("rediss://"):
    broker = broker.replace("rediss://", "redis://", 1)
if backend.startswith("rediss://"):
    backend = backend.replace("rediss://", "redis://", 1)

app.conf.update(
    broker_url=broker,
    result_backend=backend,
    broker_connection_retry_on_startup=True,
)

app.conf.broker_use_ssl = None
app.conf.redis_backend_use_ssl = None

bto = (
    dict(app.conf.broker_transport_options) if app.conf.broker_transport_options else {}
)
bto.pop("ssl", None)
app.conf.broker_transport_options = bto

logger = logging.getLogger(__name__)
logger.warning(
    "CELERY CONNECT: broker=%s backend=%s", app.conf.broker_url, app.conf.result_backend
)

app.autodiscover_tasks()
