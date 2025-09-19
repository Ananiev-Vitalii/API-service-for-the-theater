from django.views import generic
from django.utils import timezone
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic.edit import FormMixin
from django.db import IntegrityError, transaction
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_GET
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Count, F, IntegerField, BooleanField, ExpressionWrapper,
    Case, When, Value,
)

from theater.utils import ajax_only
from theater.forms import TicketForm
from theater.messages import MSG
from theater.models import Performance, Actor, Reservation, Ticket


@ajax_only
@require_GET
def performance_info(request: HttpRequest, pk: int) -> JsonResponse:
    perf = get_object_or_404(Performance.objects.select_related("theatre_hall"), pk=pk)
    hall = perf.theatre_hall
    taken = list(Ticket.objects.filter(performance=perf).values("row", "seat"))
    sold_out = len(taken) >= (hall.rows * hall.seats_in_row)

    return JsonResponse(
        {
            "rows": hall.rows,
            "seats_in_row": hall.seats_in_row,
            "taken": taken,
            "sold_out": sold_out,
        }
    )


class ActorsListView(generic.ListView):
    template_name = "includes/actors_partial.html"
    context_object_name = "actors"
    limit: int | None = 3

    def get_queryset(self) -> QuerySet[Actor]:
        qs = Actor.objects.order_by("last_name")
        return qs if self.limit is None else qs[: self.limit]


class PerformanceBaseListView(generic.ListView):
    context_object_name = "performances"
    template_name = "includes/performances_partial.html"
    limit: int | None = 3

    def get_queryset(self):
        qs = (
            Performance.objects.filter(show_time__gte=timezone.now())
            .select_related("play", "theatre_hall")
            .prefetch_related("play__genres")
            .annotate(
                reserved=Count("tickets"),
                capacity=ExpressionWrapper(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row"),
                    output_field=IntegerField(),
                ),
            )
            .annotate(
                sold_out=Case(
                    When(reserved__gte=F("capacity"), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            .order_by("show_time")
        )
        return qs if self.limit is None else qs[: self.limit]


class MyReservationsPartialView(LoginRequiredMixin, generic.ListView):
    template_name = "includes/reservations_rows.html"
    context_object_name = "my_tickets"

    def get_queryset(self):
        return (
            Ticket.objects.filter(reservation__user=self.request.user)
            .select_related(
                "performance__play", "performance__theatre_hall", "reservation"
            )
            .order_by("-reservation__created_at")
        )


# Main
class HomePageListView(FormMixin, PerformanceBaseListView):
    template_name = "theater/home.html"
    form_class = TicketForm

    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() == "POST" and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actors"] = Actor.objects.all().order_by("last_name")[:3]
        if self.request.user.is_authenticated:
            context["my_tickets"] = (
                Ticket.objects.filter(reservation__user=self.request.user)
                .select_related(
                    "reservation",
                    "performance__play",
                    "performance__theatre_hall",
                )
                .order_by("-reservation__created_at", "-id")
            )
        else:
            context["my_tickets"] = None
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        if not form.is_valid():
            if is_ajax:
                return JsonResponse(
                    {"success": False, "errors": form.errors.get_json_data()},
                    status=400,
                )

            return self.render_to_response(self.get_context_data(form=form))

        try:
            with transaction.atomic():
                reservation = Reservation.objects.create(user=request.user)
                ticket = form.save(commit=False)
                ticket.reservation = reservation
                ticket.save()
        except IntegrityError:

            if is_ajax:
                return JsonResponse(
                    {
                        "success": False,
                        "message": MSG.SEAT_TAKEN,
                        "errors": {"seat": [{"message": MSG.SEAT_TAKEN}]},
                    },
                    status=409,
                )
            form.add_error("seat", MSG.SEAT_TAKEN)
            return self.render_to_response(self.get_context_data(form=form))

        if is_ajax:
            return JsonResponse({"success": True, "message": MSG.SUCCESS})
        return self.render_to_response(self.get_context_data(form=self.get_form()))
