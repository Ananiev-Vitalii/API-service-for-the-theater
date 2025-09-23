from django.utils import timezone
from django.db import transaction
from celery import shared_task
from theater.models import Performance


@shared_task(ignore_result=True)
def purge_past_performances() -> dict:
    now = timezone.now()
    with transaction.atomic():
        qs = Performance.objects.filter(show_time__lt=now)
        deleted_count = qs.count()
        qs.delete()
    return {"deleted_performances": deleted_count, "cutoff": now.isoformat()}
