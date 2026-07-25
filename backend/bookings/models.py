from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from spaces.models import Space


class Booking(models.Model):
    """A reservation of a Space by a user for a specific date/time window."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked In"
        CHECKED_OUT = "checked_out", "Checked Out"
        CANCELLED = "cancelled", "Cancelled"

    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    # Bookings in these statuses still occupy the time slot (only a cancelled
    # booking frees it up again).
    BLOCKING_STATUSES = [Status.PENDING, Status.CONFIRMED, Status.CHECKED_IN, Status.CHECKED_OUT]

    class Meta:
        ordering = ["-date", "-start_time"]

    def __str__(self):
        return f"{self.space.name} — {self.date} {self.start_time}-{self.end_time} ({self.user})"

    def clean(self):
        super().clean()

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "End time must be after start time."})

        if self.space_id and self.date and self.start_time and self.end_time:
            overlapping = (
                Booking.objects.filter(
                    space_id=self.space_id,
                    date=self.date,
                    status__in=self.BLOCKING_STATUSES,
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time,
                )
                .exclude(pk=self.pk)
            )
            if overlapping.exists():
                raise ValidationError(
                    "This space is already booked for an overlapping time slot on that date."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Payment(models.Model):
    """The payment taken for a booking at check-out time."""

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CREDIT_CARD = "credit_card", "Credit Card"
        DEBIT_CARD = "debit_card", "Debit Card"
        WALLET = "wallet", "Digital Wallet"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=Method.choices)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.booking} — {self.get_method_display()} — {self.amount}"
