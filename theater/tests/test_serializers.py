import tempfile
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from theater.models import Actor, Genre, Play, TheatreHall, Performance, Reservation
from theater.api.v1.serializers import (
    PlayWriteSerializer,
    ReservationWriteSerializer,
    TicketWriteSerializer,
    ActorSerializer,
)

User = get_user_model()


class PlayWriteSerializerTests(TestCase):
    def setUp(self):
        self.actor1 = Actor.objects.create(first_name="A", last_name="One")
        self.actor2 = Actor.objects.create(first_name="B", last_name="Two")
        self.genre1 = Genre.objects.create(name="Drama")
        self.genre2 = Genre.objects.create(name="Comedy")

    def test_create_sets_m2m(self):
        payload = {
            "title": "Hamlet",
            "description": "desc",
            "actors": [self.actor1.id, self.actor2.id],
            "genres": [self.genre1.id, self.genre2.id],
        }
        ser = PlayWriteSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        play = ser.save()
        self.assertEqual(play.title, "Hamlet")
        self.assertSetEqual(set(play.actors.all()), {self.actor1, self.actor2})
        self.assertSetEqual(set(play.genres.all()), {self.genre1, self.genre2})

    def test_update_sets_m2m(self):
        play = Play.objects.create(title="Old", description="d")
        play.actors.set([self.actor1])
        play.genres.set([self.genre1])
        payload = {
            "title": "New",
            "actors": [self.actor2.id],
            "genres": [self.genre2.id],
        }
        ser = PlayWriteSerializer(instance=play, data=payload, partial=True)
        self.assertTrue(ser.is_valid(), ser.errors)
        play = ser.save()
        self.assertEqual(play.title, "New")
        self.assertSetEqual(set(play.actors.all()), {self.actor2})
        self.assertSetEqual(set(play.genres.all()), {self.genre2})


class ReservationWriteSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="u@example.com", password="pass12345"
        )

    def test_create_sets_user_from_request(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/reservations/")
        request.user = self.user
        ser = ReservationWriteSerializer(data={}, context={"request": request})
        self.assertTrue(ser.is_valid(), ser.errors)
        reservation = ser.save()
        self.assertEqual(reservation.user, self.user)

    def test_validate_user_blocks_other_user(self):
        other = User.objects.create_user(email="o@example.com", password="pass12345")
        factory = APIRequestFactory()
        request = factory.post("/api/v1/reservations/")
        request.user = self.user
        ser = ReservationWriteSerializer(
            data={"user": other.id}, context={"request": request}
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("user", ser.errors)


class TicketWriteSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="u@example.com", password="pass12345"
        )
        self.hall = TheatreHall.objects.create(name="H1", rows=5, seats_in_row=5)
        self.play = Play.objects.create(title="T", description="d")
        self.performance = Performance.objects.create(
            play=self.play, theatre_hall=self.hall, show_time="2030-01-01T10:00:00Z"
        )
        self.reservation = Reservation.objects.create(user=self.user)

    def test_create_ok_for_own_reservation_and_bounds(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/tickets/")
        request.user = self.user
        payload = {
            "reservation": self.reservation.id,
            "performance": self.performance.id,
            "row": 3,
            "seat": 4,
        }
        ser = TicketWriteSerializer(data=payload, context={"request": request})
        self.assertTrue(ser.is_valid(), ser.errors)
        ticket = ser.save()
        self.assertEqual(ticket.row, 3)
        self.assertEqual(ticket.seat, 4)

    def test_validate_reservation_denies_others(self):
        other = User.objects.create_user(email="o@example.com", password="pass12345")
        other_res = Reservation.objects.create(user=other)
        factory = APIRequestFactory()
        request = factory.post("/api/v1/tickets/")
        request.user = self.user
        payload = {
            "reservation": other_res.id,
            "performance": self.performance.id,
            "row": 1,
            "seat": 1,
        }
        ser = TicketWriteSerializer(data=payload, context={"request": request})
        self.assertFalse(ser.is_valid())
        self.assertIn("reservation", ser.errors)

    def test_validate_bounds(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/tickets/")
        request.user = self.user
        payload = {
            "reservation": self.reservation.id,
            "performance": self.performance.id,
            "row": 10,
            "seat": 1,
        }
        ser = TicketWriteSerializer(data=payload, context={"request": request})
        self.assertFalse(ser.is_valid())
        self.assertIn("row", ser.errors)


class ActorSerializerTests(TestCase):
    def test_avatar_url_returns_default_when_field_has_default(self):
        actor = Actor.objects.create(first_name="A", last_name="B")
        ser = ActorSerializer(actor, context={"request": None})
        self.assertIsInstance(ser.data["avatar_url"], str)
        self.assertIn("default", ser.data["avatar_url"])

    def test_avatar_url_builds_absolute_with_request(self):
        actor = Actor.objects.create(first_name="A", last_name="B")
        request = APIRequestFactory().get("/")
        ser = ActorSerializer(actor, context={"request": request})
        self.assertTrue(ser.data["avatar_url"].startswith("http://testserver"))

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_avatar_url_with_custom_file(self):
        image = SimpleUploadedFile("avatar.jpg", b"file", content_type="image/jpeg")
        actor = Actor.objects.create(first_name="A", last_name="B", avatar=image)
        ser = ActorSerializer(actor, context={"request": None})
        self.assertTrue(ser.data["avatar_url"].endswith("avatar.jpg"))
