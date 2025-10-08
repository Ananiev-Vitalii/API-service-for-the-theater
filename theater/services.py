from typing import Any
import logging
from django.urls import reverse
from django.db import transaction
from theater.tasks import send_ticket_email

logger = logging.getLogger(__name__)


def notify_ticket_booked(request: Any, reservation: Any, ticket: Any) -> None:
    home_url = request.build_absolute_uri(reverse("theater:home")) if request else None

    def _enqueue():
        try:
            send_ticket_email.delay(reservation.id, ticket.id, home_url)
        except Exception as exc:
            logger.warning("Email enqueue failed: %r", exc, exc_info=True)

    transaction.on_commit(_enqueue)
