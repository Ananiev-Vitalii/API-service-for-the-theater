from typing import Any, Dict
from django.views import generic
from django.utils import timezone
from django.db.models import QuerySet
from theater.models import Performance, Actor


class PerformanceBaseListView(generic.ListView):
    model = Performance
    context_object_name = "performances"

    def get_queryset(self) -> QuerySet[Performance]:
        queryset = (
            Performance.objects.filter(show_time__gte=timezone.now())
            .select_related("play", "theatre_hall")
            .prefetch_related("play__genres")
            .order_by("show_time")
        )
        return queryset


class TopPerformancesListView(PerformanceBaseListView):
    template_name = "includes/performances_partial.html"

    def get_queryset(self) -> QuerySet[Performance]:
        return super().get_queryset()[:3]


class AllPerformancesListView(PerformanceBaseListView):
    template_name = "includes/performances_partial.html"


class HomePageListView(TopPerformancesListView):
    template_name = "theater/home.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["actors"] = Actor.objects.all().order_by("last_name")[:3]
        return context


class AllActorsListView(generic.ListView):
    model = Actor
    template_name = "includes/actors_partial.html"
    context_object_name = "actors"

    def get_queryset(self) -> QuerySet[Actor]:
        return Actor.objects.order_by("last_name")


class TopActorsListView(AllActorsListView):
    def get_queryset(self) -> QuerySet[Actor]:
        return super().get_queryset()[:3]
