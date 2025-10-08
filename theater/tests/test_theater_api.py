from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from theater.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)

User = get_user_model()

ACTOR_LIST = reverse("api_v1:actor-list")
GENRE_LIST = reverse("api_v1:genre-list")
HALL_LIST = reverse("api_v1:hall-list")
PLAY_LIST = reverse("api_v1:play-list")
PERFORMANCE_LIST = reverse("api_v1:performance-list")
RESERVATION_LIST = reverse("api_v1:reservation-list")
TICKET_LIST = reverse("api_v1:ticket-list")


def detail_url(name, pk):
    return reverse(f"api_v1:{name}-detail", args=[pk])


def results(res):
    return res.data if isinstance(res.data, list) else res.data.get("results", res.data)


class TheaterApiAnonTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_public_endpoints_requirements(self):
        res_a = self.client.get(ACTOR_LIST)
        res_g = self.client.get(GENRE_LIST)
        res_h = self.client.get(HALL_LIST)
        self.assertIn(
            res_a.status_code,
            (
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )
        self.assertIn(
            res_g.status_code,
            (
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )
        self.assertIn(
            res_h.status_code,
            (
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_reservations_requires_auth(self):
        res = self.client.get(RESERVATION_LIST)
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )

    def test_tickets_requires_auth(self):
        res = self.client.get(TICKET_LIST)
        self.assertIn(
            res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        )


class TheaterApiAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="u@example.com", password="pass12345", first_name="F", last_name="L"
        )
        self.client.force_authenticate(self.user)

    def test_actors_list_and_retrieve(self):
        a = Actor.objects.create(first_name="A", last_name="One")
        Actor.objects.create(first_name="B", last_name="Two")
        res = self.client.get(ACTOR_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(a.id, ids)
        url = detail_url("actor", a.id)
        r2 = self.client.get(url)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data["id"], a.id)

    def test_genres_list(self):
        g1 = Genre.objects.create(name="Drama")
        Genre.objects.create(name="Comedy")
        res = self.client.get(GENRE_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(g1.id, ids)

    def test_halls_list(self):
        h = TheatreHall.objects.create(name="H1", rows=5, seats_in_row=5)
        res = self.client.get(HALL_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(h.id, ids)

    def test_plays_list_filter_by_genre(self):
        g1 = Genre.objects.create(name="Drama")
        g2 = Genre.objects.create(name="Comedy")
        p1 = Play.objects.create(title="P1", description="d")
        p2 = Play.objects.create(title="P2", description="d")
        p1.genres.add(g1)
        p2.genres.add(g2)
        res = self.client.get(PLAY_LIST, {"genres": g1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(p1.id, ids)
        self.assertNotIn(p2.id, ids)

    def test_performances_list_and_filter_by_hall(self):
        h1 = TheatreHall.objects.create(name="H1", rows=5, seats_in_row=5)
        h2 = TheatreHall.objects.create(name="H2", rows=5, seats_in_row=5)
        p = Play.objects.create(title="T", description="d")
        perf1 = Performance.objects.create(
            play=p, theatre_hall=h1, show_time="2030-01-01T10:00:00Z"
        )
        Performance.objects.create(
            play=p, theatre_hall=h2, show_time="2030-01-02T10:00:00Z"
        )
        res = self.client.get(PERFORMANCE_LIST, {"theatre_hall": h1.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(perf1.id, ids)

    def test_reservations_user_sees_only_own(self):
        my_res = Reservation.objects.create(user=self.user)
        other = User.objects.create_user(email="o@example.com", password="pass12345")
        Reservation.objects.create(user=other)
        res = self.client.get(RESERVATION_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(my_res.id, ids)
        self.assertEqual(len(ids), 1)

    def test_reservation_create_sets_user(self):
        res = self.client.post(RESERVATION_LIST, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["user"], self.user.id)

    def test_reservation_create_other_user_forbidden(self):
        other = User.objects.create_user(email="o@example.com", password="pass12345")
        res = self.client.post(RESERVATION_LIST, {"user": other.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tickets_user_only_own_and_filter_by_performance(self):
        h = TheatreHall.objects.create(name="H1", rows=5, seats_in_row=5)
        p = Play.objects.create(title="T", description="d")
        perf = Performance.objects.create(
            play=p, theatre_hall=h, show_time="2030-01-01T10:00:00Z"
        )
        my_res = Reservation.objects.create(user=self.user)
        t1 = Ticket.objects.create(reservation=my_res, performance=perf, row=1, seat=1)
        other = User.objects.create_user(email="o@example.com", password="pass12345")
        other_res = Reservation.objects.create(user=other)
        Ticket.objects.create(reservation=other_res, performance=perf, row=1, seat=2)
        res = self.client.get(TICKET_LIST, {"performance": perf.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertIn(t1.id, ids)
        self.assertEqual(len(ids), 1)

    def test_ticket_create_validates_bounds_and_ownership(self):
        h = TheatreHall.objects.create(name="H1", rows=5, seats_in_row=5)
        p = Play.objects.create(title="T", description="d")
        perf = Performance.objects.create(
            play=p, theatre_hall=h, show_time="2030-01-01T10:00:00Z"
        )
        my_res = Reservation.objects.create(user=self.user)
        payload = {
            "reservation": my_res.id,
            "performance": perf.id,
            "row": 6,
            "seat": 1,
        }
        r1 = self.client.post(TICKET_LIST, payload, format="json")
        self.assertEqual(r1.status_code, status.HTTP_400_BAD_REQUEST)
        payload_ok = {
            "reservation": my_res.id,
            "performance": perf.id,
            "row": 2,
            "seat": 2,
        }
        r2 = self.client.post(TICKET_LIST, payload_ok, format="json")
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        other = User.objects.create_user(email="o@example.com", password="pass12345")
        other_res = Reservation.objects.create(user=other)
        r3 = self.client.post(
            TICKET_LIST,
            {"reservation": other_res.id, "performance": perf.id, "row": 1, "seat": 3},
            format="json",
        )
        self.assertEqual(r3.status_code, status.HTTP_400_BAD_REQUEST)


class TheaterApiAdminTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@example.com", password="pass12345", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_admin_create_play_with_relations(self):
        a1 = Actor.objects.create(first_name="A", last_name="One")
        g1 = Genre.objects.create(name="Drama")
        payload = {
            "title": "AdminPlay",
            "description": "d",
            "actors": [a1.id],
            "genres": [g1.id],
        }
        res = self.client.post(PLAY_LIST, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.title, "AdminPlay")
        self.assertEqual(list(play.actors.values_list("id", flat=True)), [a1.id])
        self.assertEqual(list(play.genres.values_list("id", flat=True)), [g1.id])

    def test_admin_create_performance(self):
        h = TheatreHall.objects.create(name="H1", rows=5, seats_in_row=5)
        p = Play.objects.create(title="T", description="d")
        payload = {
            "play": p.id,
            "theatre_hall": h.id,
            "show_time": "2030-01-01T10:00:00Z",
        }
        res = self.client.post(PERFORMANCE_LIST, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        perf = Performance.objects.get(id=res.data["id"])
        self.assertEqual(perf.play_id, p.id)
        self.assertEqual(perf.theatre_hall_id, h.id)

    def test_admin_reservations_list_all(self):
        u1 = User.objects.create_user(email="u1@example.com", password="pass12345")
        u2 = User.objects.create_user(email="u2@example.com", password="pass12345")
        r1 = Reservation.objects.create(user=u1)
        r2 = Reservation.objects.create(user=u2)
        res = self.client.get(RESERVATION_LIST)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in results(res)]
        self.assertCountEqual(ids, [r1.id, r2.id])
