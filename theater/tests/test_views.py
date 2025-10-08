from datetime import timedelta
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from theater.models import (
    Actor,
    Play,
    Genre,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)
from theater.views import (
    performance_info,
    ActorsListView,
    PerformanceBaseListView,
    MyReservationsPartialView,
    HomePageListView,
    custom_page_not_found_view,
)
from theater.messages import MSG


class ViewsSetupMixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="pass12345"
        )

        self.actor1 = Actor.objects.create(first_name="A", last_name="Alpha")
        self.actor2 = Actor.objects.create(first_name="B", last_name="Beta")
        self.actor3 = Actor.objects.create(first_name="C", last_name="Gamma")
        self.actor4 = Actor.objects.create(first_name="D", last_name="Delta")

        self.genre = Genre.objects.create(name="Drama")
        self.play = Play.objects.create(title="Hamlet", description="Desc")
        self.play.actors.add(self.actor1, self.actor2, self.actor3)
        self.play.genres.add(self.genre)

        self.hall = TheatreHall.objects.create(name="Main", rows=2, seats_in_row=3)

        now = timezone.now()
        self.perf1 = Performance.objects.create(
            play=self.play, theatre_hall=self.hall, show_time=now + timedelta(hours=1)
        )
        self.perf2 = Performance.objects.create(
            play=self.play, theatre_hall=self.hall, show_time=now + timedelta(hours=2)
        )


class AjaxPerformanceInfoTests(ViewsSetupMixin):
    def test_performance_info_json_payload(self):
        res = Reservation.objects.create(user=self.user)
        Ticket.objects.create(performance=self.perf1, reservation=res, row=1, seat=2)

        req = self.factory.get(
            f"/api/performance-info/{self.perf1.pk}/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        resp = performance_info(req, pk=self.perf1.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode())
        self.assertEqual(data["rows"], self.hall.rows)
        self.assertEqual(data["seats_in_row"], self.hall.seats_in_row)
        self.assertIn({"row": 1, "seat": 2}, data["taken"])
        self.assertFalse(data["sold_out"])

    def test_performance_info_sold_out(self):
        res = Reservation.objects.create(user=self.user)
        for r in (1, 2):
            for s in (1, 2, 3):
                Ticket.objects.create(
                    performance=self.perf1, reservation=res, row=r, seat=s
                )

        req = self.factory.get(
            f"/api/performance-info/{self.perf1.pk}/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        resp = performance_info(req, pk=self.perf1.pk)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode())
        self.assertTrue(data["sold_out"])


class ActorsListViewTests(ViewsSetupMixin):
    def test_get_queryset_limit_and_order(self):
        view = ActorsListView()
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 3)
        self.assertEqual(
            list(qs.values_list("last_name", flat=True)),
            ["Alpha", "Beta", "Delta"],
        )


class PerformanceBaseListViewTests(ViewsSetupMixin):
    def test_get_queryset_annotations_and_limit(self):
        view = PerformanceBaseListView()
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 2)
        obj = qs.first()
        self.assertTrue(hasattr(obj, "reserved"))
        self.assertTrue(hasattr(obj, "capacity"))
        self.assertTrue(hasattr(obj, "sold_out"))


class MyReservationsPartialViewTests(ViewsSetupMixin):
    def test_requires_login(self):
        request = self.factory.get("/includes/reservations/")
        request.user = AnonymousUser()
        response = MyReservationsPartialView.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_returns_rows_for_user(self):
        request = self.factory.get("/includes/reservations/")
        request.user = self.user
        res = Reservation.objects.create(user=self.user)
        Ticket.objects.create(performance=self.perf1, reservation=res, row=1, seat=1)
        response = MyReservationsPartialView.as_view()(request)
        self.assertEqual(response.status_code, 200)


class HomePageListViewTests(ViewsSetupMixin):
    def test_home_get_for_anonymous(self):
        url = reverse("theater:home")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("performances", resp.context)
        self.assertIn("actors", resp.context)
        self.assertIsNone(resp.context["my_tickets"])

    def test_home_post_requires_login(self):
        url = reverse("theater:home")
        resp = self.client.post(
            url, data={"performance": self.perf1.pk, "row": 1, "seat": 1}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_home_post_ajax_success(self):
        self.client.login(username="user@example.com", password="pass12345")
        url = reverse("theater:home")
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        resp = self.client.post(
            url, data={"performance": self.perf1.pk, "row": 1, "seat": 1}, **headers
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content.decode())
        self.assertTrue(data.get("success"))
        self.assertTrue(Reservation.objects.filter(user=self.user).exists())
        self.assertTrue(
            Ticket.objects.filter(performance=self.perf1, row=1, seat=1).exists()
        )

    def test_home_post_ajax_conflict(self):
        """Form-level validation may return 400; DB constraint path returns 409. Accept either and assert message."""
        self.client.login(username="user@example.com", password="pass12345")
        res = Reservation.objects.create(user=self.user)
        Ticket.objects.create(performance=self.perf1, reservation=res, row=1, seat=1)

        url = reverse("theater:home")
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        resp = self.client.post(
            url, data={"performance": self.perf1.pk, "row": 1, "seat": 1}, **headers
        )
        self.assertIn(resp.status_code, (400, 409))
        data = json.loads(resp.content.decode())
        # 409 path has "message"; 400 path has form "errors"
        msg = data.get("message", "")
        if not msg:
            errs = data.get("errors") or {}
            msg = " ".join(
                (e.get("message", "") if isinstance(e, dict) else str(e))
                for arr in errs.values()
                for e in arr
            )
        self.assertIn(MSG.SEAT_TAKEN, msg)

    def test_home_get_form_sets_filtered_performance_queryset(self):
        request = self.factory.get(reverse("theater:home"))
        request.user = self.user
        view = HomePageListView()
        view.request = request

        form = view.get_form()
        self.assertIn("performance", form.fields)

        qs = form.fields["performance"].queryset
        self.assertTrue(qs.exists())
        for p in qs:
            self.assertTrue(hasattr(p, "reserved"))
            self.assertTrue(hasattr(p, "capacity"))
            self.assertLess(p.reserved, p.capacity)


class Custom404ViewTests(TestCase):
    @override_settings(DEBUG=False)
    def test_custom_404_view_returns_404(self):
        req = RequestFactory().get("/non-existing/")
        resp = custom_page_not_found_view(req, exception=Http404())
        self.assertEqual(resp.status_code, 404)
