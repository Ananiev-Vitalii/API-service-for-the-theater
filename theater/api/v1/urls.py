from django.urls import path, include
from rest_framework import routers

from theater.api.v1.views import (
    ActorViewSet,
    GenreViewSet,
    PlayViewSet,
    TheatreHallViewSet,
    PerformanceViewSet,
    ReservationViewSet,
    TicketViewSet,
)

app_name = "api_v1"

router = routers.DefaultRouter()
router.register("plays", PlayViewSet, basename="play")
router.register("actors", ActorViewSet, basename="actor")
router.register("genres", GenreViewSet, basename="genre")
router.register("tickets", TicketViewSet, basename="ticket")
router.register("halls", TheatreHallViewSet, basename="hall")
router.register("reservations", ReservationViewSet, basename="reservation")
router.register("performances", PerformanceViewSet, basename="performance")


urlpatterns = [
    path("", include(router.urls)),
]
