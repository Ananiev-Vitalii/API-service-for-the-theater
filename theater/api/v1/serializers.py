from django.contrib.auth import get_user_model
from rest_framework import serializers
from typing import Optional

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


class ActorSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name", "avatar", "avatar_url"]
        extra_kwargs = {
            "avatar": {"write_only": True, "required": False},
        }

    def get_full_name(self, obj: "Actor") -> str:
        return f"{obj.first_name} {obj.last_name}"

    def get_avatar_url(self, obj: "Actor") -> Optional[str]:
        if not obj.avatar:
            return None
        request = self.context.get("request")
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ("id", "name")


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row")


class _PlayBaseSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Play
        fields = ("id", "title", "description", "image", "image_url")
        extra_kwargs = {
            "image": {"write_only": True, "required": False},
        }

    def get_image_url(self, obj: Play) -> Optional[str]:
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class PlayListSerializer(_PlayBaseSerializer):
    actors = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    genres = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(_PlayBaseSerializer.Meta):
        fields = _PlayBaseSerializer.Meta.fields + ("actors", "genres")


class PlayWriteSerializer(_PlayBaseSerializer):
    actors = serializers.PrimaryKeyRelatedField(queryset=Actor.objects.all(), many=True)
    genres = serializers.PrimaryKeyRelatedField(queryset=Genre.objects.all(), many=True)

    class Meta(_PlayBaseSerializer.Meta):
        fields = _PlayBaseSerializer.Meta.fields + ("actors", "genres")

    def create(self, validated_data: dict) -> Play:
        actors = validated_data.pop("actors", [])
        genres = validated_data.pop("genres", [])
        play = Play.objects.create(**validated_data)
        if actors:
            play.actors.set(actors)
        if genres:
            play.genres.set(genres)
        return play

    def update(self, instance: Play, validated_data: dict) -> Play:
        actors = validated_data.pop("actors", None)
        genres = validated_data.pop("genres", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if actors is not None:
            instance.actors.set(actors)
        if genres is not None:
            instance.genres.set(genres)
        return instance


class PlayRetrieveSerializer(_PlayBaseSerializer):
    actors_detail = ActorSerializer(source="actors", many=True, read_only=True)
    genres_detail = GenreSerializer(source="genres", many=True, read_only=True)

    class Meta(_PlayBaseSerializer.Meta):
        fields = _PlayBaseSerializer.Meta.fields + ("actors_detail", "genres_detail")


class PerformanceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall")


class PerformanceRetrieveSerializer(serializers.ModelSerializer):
    play_detail = PlayRetrieveSerializer(source="play", read_only=True)
    theatre_hall_detail = TheatreHallSerializer(source="theatre_hall", read_only=True)

    class Meta:
        model = Performance
        fields = ("id", "show_time", "play_detail", "theatre_hall_detail")


class PerformanceWriteSerializer(PerformanceListSerializer):
    play = serializers.PrimaryKeyRelatedField(queryset=Play.objects.all())
    theatre_hall = serializers.PrimaryKeyRelatedField(
        queryset=TheatreHall.objects.all()
    )


class ReservationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ("id", "created_at", "user")


class ReservationRetrieveSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "user", "email", "first_name", "last_name")


class ReservationWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "user")
        read_only_fields = ("created_at",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            if (
                "user" in self.fields
                and getattr(self.fields["user"], "queryset", None) is not None
            ):
                self.fields["user"].queryset = User.objects.filter(pk=request.user.pk)

    def validate_user(self, value: User) -> User:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_staff and value.pk != user.pk:
            raise serializers.ValidationError(
                "You can operate only on your own reservations."
            )
        return value

    def create(self, validated_data: dict) -> Reservation:
        request = self.context.get("request")
        if request and request.user.is_authenticated and "user" not in validated_data:
            validated_data["user"] = request.user
        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance", "reservation")


class TicketRetrieveSerializer(serializers.ModelSerializer):

    performance_detail = PerformanceRetrieveSerializer(
        source="performance", read_only=True
    )
    reservation_detail = ReservationRetrieveSerializer(
        source="reservation", read_only=True
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance_detail", "reservation_detail")


class TicketWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "reservation", "performance", "row", "seat")
        validators = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields["reservation"].queryset = Reservation.objects.filter(
                user=request.user
            )

    def validate_reservation(self, value: Reservation) -> Reservation:
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            if value.user_id != request.user.id:
                raise serializers.ValidationError(
                    "You can use only your own reservations."
                )
        return value

    def validate(self, attrs: dict) -> dict:
        performance = attrs.get("performance") or getattr(
            self.instance, "performance", None
        )
        row = attrs.get("row", getattr(self.instance, "row", None))
        seat = attrs.get("seat", getattr(self.instance, "seat", None))

        if performance is not None:
            hall = performance.theatre_hall
            errors = {}
            if row is not None and row > hall.rows:
                errors["row"] = f"Row must be between 1 and {hall.rows}."
            if seat is not None and seat > hall.seats_in_row:
                errors["seat"] = f"Seat must be between 1 and {hall.seats_in_row}."
            if errors:
                raise serializers.ValidationError(errors)

        return attrs
