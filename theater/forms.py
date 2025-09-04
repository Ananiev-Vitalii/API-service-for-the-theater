from django import forms
from django.utils import timezone
from theater.models import Ticket, Performance
from django.db.models import Count, F, IntegerField, ExpressionWrapper


class PerformanceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Performance) -> str:
        return obj.play.title


class TicketForm(forms.ModelForm):
    performance = PerformanceChoiceField(
        queryset=Performance.objects.none(),
        label="Performance",
        empty_label="Select performance",
    )
    row = forms.TypedChoiceField(label="Row", coerce=int)
    seat = forms.TypedChoiceField(label="Seat", coerce=int)

    class Meta:
        model = Ticket
        fields = ["performance", "row", "seat"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        perf_qs = (
            Performance.objects.filter(show_time__gte=timezone.now())
            .select_related("play", "theatre_hall")
            .annotate(
                reserved=Count("tickets"),
                capacity=ExpressionWrapper(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row"),
                    output_field=IntegerField(),
                ),
            )
            .filter(reserved__lt=F("capacity"))
            .order_by("show_time")
        )
        self.fields["performance"].queryset = perf_qs
        self.fields["row"].choices = []
        self.fields["seat"].choices = []

        if self.is_bound:
            perf_id = (self.data or self.initial).get("performance")
            if perf_id:
                try:
                    perf = Performance.objects.select_related("theatre_hall").get(
                        pk=perf_id
                    )
                except Performance.DoesNotExist:
                    return
                hall = perf.theatre_hall
                self.fields["row"].choices = [
                    (r, str(r)) for r in range(1, hall.rows + 1)
                ]
                self.fields["seat"].choices = [
                    (s, str(s)) for s in range(1, hall.seats_in_row + 1)
                ]
