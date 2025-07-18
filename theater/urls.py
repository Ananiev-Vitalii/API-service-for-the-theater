from django.urls import path
from theater.views import (
    HomePageListView,
    AllPerformancesListView,
    TopPerformancesListView,
    TopActorsListView,
    AllActorsListView,
)

app_name = "theater"

urlpatterns = [
    # Main
    path("", HomePageListView.as_view(), name="home"),
    # AJAX endpoints
    path(
        "performances/all/", AllPerformancesListView.as_view(), name="all_performances"
    ),
    path(
        "performances/top/", TopPerformancesListView.as_view(), name="top_performances"
    ),
    path("actors/top/", TopActorsListView.as_view(), name="top-actors"),
    path("actors/all/", AllActorsListView.as_view(), name="all-actors"),
]
