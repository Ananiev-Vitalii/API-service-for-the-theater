from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
)

from theater.api.v1.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlayListSerializer,
    PlayRetrieveSerializer,
    PlayWriteSerializer,
    TheatreHallSerializer,
    PerformanceListSerializer,
    PerformanceRetrieveSerializer,
    PerformanceWriteSerializer,
    ReservationListSerializer,
    ReservationRetrieveSerializer,
    ReservationWriteSerializer,
    TicketListSerializer,
    TicketRetrieveSerializer,
    TicketWriteSerializer,
)
from theater.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all().order_by("last_name", "first_name")
    serializer_class = ActorSerializer


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all().order_by("name")
    serializer_class = GenreSerializer


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all().order_by("name")
    serializer_class = TheatreHallSerializer


@extend_schema_view(
    list=extend_schema(
        description="List plays. Supports filtering by a single genre.",
        parameters=[
            OpenApiParameter(
                name="genres",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by a single genre id. Example: ?genres=2",
                examples=[OpenApiExample("Genre id", value=2)],
            ),
        ],
    )
)
class PlayViewSet(viewsets.ModelViewSet):
    queryset = (
        Play.objects.all()
        .prefetch_related("actors", "genres")
        .order_by("title")
        .distinct()
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"genres": ["exact"]}

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        if self.action == "retrieve":
            return PlayRetrieveSerializer
        return PlayWriteSerializer


@extend_schema_view(
    list=extend_schema(
        description="List performances. Supports filtering by theatre hall.",
        parameters=[
            OpenApiParameter(
                name="theatre_hall",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by theatre hall id. Example: `?theatre_hall=3`.",
                examples=[OpenApiExample("Hall id", value=3)],
            ),
        ],
    )
)
class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects.select_related("play", "theatre_hall")
        .prefetch_related("play__actors", "play__genres")
        .order_by("show_time")
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["theatre_hall"]

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceRetrieveSerializer
        return PerformanceWriteSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Reservation.objects.select_related("user")
            .prefetch_related(
                "tickets", "tickets__performance", "tickets__performance__play"
            )
            .order_by("-created_at")
        )
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        return qs if user.is_staff else qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        if self.action == "retrieve":
            return ReservationRetrieveSerializer
        return ReservationWriteSerializer


@extend_schema_view(
    list=extend_schema(
        description="List tickets. Supports filtering by performance.",
        parameters=[
            OpenApiParameter(
                name="performance",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by performance id. Example: `?performance=10`.",
                examples=[OpenApiExample("Performance id", value=10)],
            ),
        ],
    )
)
class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["performance"]

    def get_queryset(self):
        qs = (
            Ticket.objects.select_related(
                "reservation",
                "reservation__user",
                "performance",
                "performance__theatre_hall",
                "performance__play",
            )
            .prefetch_related("performance__play__actors", "performance__play__genres")
            .order_by("performance__show_time", "row", "seat")
        )
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        return qs if user.is_staff else qs.filter(reservation__user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketWriteSerializer
