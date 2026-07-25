from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from spaces.models import Space
from spaces.serializers import SpaceSerializer

from .models import Booking, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "booking", "method", "amount", "paid_at"]
        read_only_fields = fields


class BookingSerializer(serializers.ModelSerializer):
    """
    Creates/reads bookings. `space` accepts a Space id on write; `space_detail`
    returns the full nested space object on read so the frontend doesn't need
    a second request.
    """

    space = serializers.SlugRelatedField(
        queryset=Space.objects.filter(is_active=True),
        slug_field="slug",
    )
    space_detail = SpaceSerializer(source="space", read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "space",
            "space_detail",
            "user",
            "date",
            "start_time",
            "end_time",
            "status",
            "payment",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def get_payment(self, obj):
        payment = getattr(obj, "payment", None)
        return PaymentSerializer(payment).data if payment else None

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("You cannot book a date in the past.")
        return value

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        space = attrs.get("space", getattr(self.instance, "space", None))
        date = attrs.get("date", getattr(self.instance, "date", None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        if space and date and start_time and end_time:
            overlapping = Booking.objects.filter(
                space=space,
                date=date,
                status__in=Booking.BLOCKING_STATUSES,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance is not None:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise serializers.ValidationError(
                    "This space is already booked for an overlapping time slot on that date."
                )

        return attrs

    def _save_and_translate_errors(self, save_fn, **kwargs):
        try:
            return save_fn(**kwargs)
        except DjangoValidationError as exc:
            # Defense-in-depth: the model's own full_clean() re-checks the same
            # invariants at save time in case of a race between validate() and commit.
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    def create(self, validated_data):
        return self._save_and_translate_errors(super().create, validated_data=validated_data)

    def update(self, instance, validated_data):
        return self._save_and_translate_errors(super().update, instance=instance, validated_data=validated_data)


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Lets a space owner/staff member confirm or cancel a booking. Checking in
    and out go through the dedicated /check-in/ and /check-out/ actions
    instead, since those enforce timing and payment rules.
    """

    class Meta:
        model = Booking
        fields = ["id", "status"]

    def validate_status(self, value):
        allowed = {Booking.Status.PENDING, Booking.Status.CONFIRMED, Booking.Status.CANCELLED}
        if value not in allowed:
            raise serializers.ValidationError(
                "Use the check-in/check-out endpoints to move a booking to that status."
            )
        return value


class CheckOutSerializer(serializers.Serializer):
    """Input for POST /bookings/{id}/check-out/ — which payment method was used."""

    payment_method = serializers.ChoiceField(choices=Payment.Method.choices)


class BookingWriteSerializer(serializers.ModelSerializer):
    """Write-only serializer — only the fields a client actually sends."""

    space = serializers.SlugRelatedField(
        queryset=Space.objects.filter(is_active=True),
        slug_field="slug",
        help_text="Space slug — get the list from GET /api/spaces/choices/",
    )

    class Meta:
        model = Booking
        fields = ["space", "date", "start_time", "end_time"]


class BookingCreateSerializer(serializers.Serializer):
    """Used only for Swagger request body on create/update — shows only the writable fields."""

    space = serializers.IntegerField(help_text="ID of the space to book")
    date = serializers.DateField(help_text="Booking date (YYYY-MM-DD)")
    start_time = serializers.TimeField(help_text="Start time e.g. 09:00")
    end_time = serializers.TimeField(help_text="End time e.g. 11:00")


class EmptySerializer(serializers.Serializer):
    """Used for actions that need no request body (e.g. check-in)."""
    pass
