from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from theater.models import Performance, Reservation, Ticket


@shared_task(ignore_result=True)
def purge_past_performances() -> dict:
    now = timezone.now()
    with transaction.atomic():
        qs = Performance.objects.filter(show_time__lt=now)
        deleted_count = qs.count()
        qs.delete()
    return {"deleted_performances": deleted_count, "cutoff": now.isoformat()}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_ticket_email(
    self, reservation_id: int, ticket_id: int, home_url: str | None = None
) -> None:
    r = Reservation.objects.select_related("user").get(id=reservation_id)
    t = Ticket.objects.select_related(
        "performance__play", "performance__theatre_hall"
    ).get(id=ticket_id)

    site_name = getattr(settings, "SITE_NAME", "Wildfire Stageworks")
    user_first = r.user.first_name or ""
    user_last = r.user.last_name or ""
    user_full = (user_first + " " + user_last).strip() or r.user.email

    ctx = {
        "site_name": site_name,
        "user_first": user_first,
        "user_last": user_last,
        "user_full": user_full,
        "reservation_id": r.id,
        "play_title": t.performance.play.title,
        "hall_name": t.performance.theatre_hall.name,
        "show_time": t.performance.show_time,
        "row": t.row,
        "seat": t.seat,
        "home_url": home_url,
    }

    subject = f"[{site_name}] Reservation №{r.id}: {ctx['play_title']} — {ctx['show_time']:%Y-%m-%d %H:%M}"
    text = render_to_string("email/ticket_booked.txt", ctx)
    html = render_to_string("email/ticket_booked.html", ctx)

    from_email = (
        getattr(settings, "DEFAULT_FROM_EMAIL", None) or settings.EMAIL_HOST_USER
    )
    msg = EmailMultiAlternatives(subject, text, from_email, [r.user.email])
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)
