from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from django.db import models
import os

from theater.messages import MSG


def actor_directory_path(instance: "Actor", filename: str) -> str:
    actor_slug = slugify(f"{instance.first_name}_{instance.last_name}")
    return os.path.join("actors", actor_slug, filename)


def play_directory_path(instance: "Play", filename: str) -> str:
    play_slug = slugify(f"{instance.title}")
    return os.path.join("plays", play_slug, filename)


class Actor(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    avatar = models.ImageField(
        upload_to=actor_directory_path, default="actors/default.png"
    )

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Play(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=255)
    actors = models.ManyToManyField(Actor, related_name="plays")
    genres = models.ManyToManyField(Genre, related_name="plays")
    image = models.ImageField(
        upload_to=play_directory_path, default="plays/default.png"
    )

    def __str__(self) -> str:
        return self.title


class TheatreHall(models.Model):
    name = models.CharField(max_length=20)
    rows = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    seats_in_row = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self) -> str:
        return self.name


class Performance(models.Model):
    play = models.ForeignKey(
        Play, on_delete=models.CASCADE, related_name="performances"
    )
    theatre_hall = models.ForeignKey(
        TheatreHall, on_delete=models.CASCADE, related_name="performances"
    )
    show_time = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.play.title} at {self.show_time}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations"
    )

    def __str__(self) -> str:
        return f"Reservation #{self.id} by {self.user}"


class Ticket(models.Model):
    row = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    seat = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    performance = models.ForeignKey(
        Performance, on_delete=models.CASCADE, related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="uniq_performance_row_seat",
                violation_error_message=MSG.SEAT_TAKEN,
            )
        ]

    def __str__(self) -> str:
        return f"Ticket for {self.performance} - Row {self.row} Seat {self.seat}"

    def clean(self) -> None:
        if not self.performance_id or self.row is None or self.seat is None:
            return

        hall = self.performance.theatre_hall

        errors = {
            "row": (
                f"Row must be between 1 and {hall.rows}."
                if self.row > hall.rows
                else None
            ),
            "seat": (
                f"Seat must be between 1 and {hall.seats_in_row}."
                if self.seat > hall.seats_in_row
                else None
            ),
        }
        errors = {k: v for k, v in errors.items() if v}

        if errors:
            raise ValidationError(errors)
