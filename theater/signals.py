from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from theater.models import Ticket, Reservation


@receiver(post_delete, sender=Ticket, dispatch_uid="theater.cleanup_empty_reservation")
def cleanup_empty_reservation(sender, instance: Ticket, **kwargs) -> None:
    res_id = instance.reservation_id
    if not res_id:
        return

    def _do_cleanup() -> None:
        if not Ticket.objects.filter(reservation_id=res_id).exists():
            Reservation.objects.filter(pk=res_id).delete()

    transaction.on_commit(_do_cleanup)
