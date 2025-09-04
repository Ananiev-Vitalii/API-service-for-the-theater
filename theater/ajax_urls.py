from django.urls import path
from theater.utils import ajax_only
from theater.views import (
    PerformanceBaseListView,
    ActorsListView,
)

app_name = "ajax"

urlpatterns = [
    path(
        "performances/top/",
        ajax_only(PerformanceBaseListView.as_view(limit=3)),
        name="performances-top",
    ),
    path(
        "performances/all/",
        ajax_only(PerformanceBaseListView.as_view(limit=None)),
        name="performances-all",
    ),
    path(
        "actors/all/", ajax_only(ActorsListView.as_view(limit=None)), name="actors-all"
    ),
    path("actors/top/", ajax_only(ActorsListView.as_view(limit=3)), name="actors-top"),
]
