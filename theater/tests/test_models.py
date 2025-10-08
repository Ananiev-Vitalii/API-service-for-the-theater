from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from theater.models import (
    Actor,
    Play,
    Genre,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)


class ModelsBasicsTests(TestCase):
    """Basic invariants and constraints for models."""

    def setUp(self):
        # User
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="pass12345"
        )
        # Reference data
        self.actor = Actor.objects.create(first_name="John", last_name="Smith")
        self.genre = Genre.objects.create(name="Drama")
        self.play = Play.objects.create(title="Hamlet", description="Desc")
        self.play.actors.add(self.actor)
        self.play.genres.add(self.genre)
        self.hall = TheatreHall.objects.create(name="Main", rows=2, seats_in_row=3)

        # Future performance
        self.perf = Performance.objects.create(
            play=self.play,
            theatre_hall=self.hall,
            show_time=timezone.now() + timedelta(hours=1),
        )

    def test_ticket_unique_constraint(self):
        """Cannot sell the same seat twice for the same performance."""
        res = Reservation.objects.create(user=self.user)
        Ticket.objects.create(performance=self.perf, reservation=res, row=1, seat=1)
        with self.assertRaises(IntegrityError):
            Ticket.objects.create(performance=self.perf, reservation=res, row=1, seat=1)

    def test_ticket_clean_validates_row_and_seat_ranges(self):
        """clean() validates row/seat ranges against hall capacity."""
        res = Reservation.objects.create(user=self.user)

        t1 = Ticket(performance=self.perf, reservation=res, row=99, seat=1)
        with self.assertRaises(ValidationError) as exc:
            t1.clean()
        self.assertIn("row", exc.exception.error_dict)

        t2 = Ticket(performance=self.perf, reservation=res, row=1, seat=99)
        with self.assertRaises(ValidationError) as exc:
            t2.clean()
        self.assertIn("seat", exc.exception.error_dict)

    def test_str_methods(self):
        """__str__ returns meaningful strings and does not crash."""
        self.assertIn("John", str(self.actor))
        self.assertIn("Hamlet", str(self.play))
        self.assertIn("Main", str(self.hall))
        self.assertIn("Hamlet", str(self.perf))
        res = Reservation.objects.create(user=self.user)
        t = Ticket.objects.create(performance=self.perf, reservation=res, row=1, seat=2)
        self.assertIn("Row 1 Seat 2", str(t))
