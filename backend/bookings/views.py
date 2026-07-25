from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Booking, Payment
from .permissions import IsOwnerOrStaff
from .serializers import BookingCreateSerializer, BookingSerializer, BookingStatusUpdateSerializer, BookingWriteSerializer, CheckOutSerializer, EmptySerializer, PaymentSerializer


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    list: List the authenticated user's own bookings (staff see every booking).
    create: Reserve a space for a date/time window. Overlapping bookings are rejected.
    retrieve/update/destroy: Manage a single booking you own (or any booking, if staff).
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "space", "date"]

    def get_queryset(self):
        queryset = Booking.objects.select_related("space", "user")
        if getattr(self, "swagger_fake_view", False):
            return queryset.none()

        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        # drf-yasg calls this with swagger_fake_view=True to build the schema.
        # Return a minimal serializer per action so Swagger shows only the fields
        # the client actually needs to send. Real requests keep BookingSerializer.
        if getattr(self, "swagger_fake_view", False):
            if self.action in ("create", "update", "partial_update"):
                return BookingWriteSerializer
            if self.action == "check_in":
                return EmptySerializer
            if self.action == "check_out":
                return CheckOutSerializer
        return BookingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(operation_summary="List my bookings", tags=["Bookings"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Create a booking", tags=["Bookings"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve a booking", tags=["Bookings"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update a booking", tags=["Bookings"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Cancel/delete a booking", tags=["Bookings"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        method="patch",
        operation_summary="Change booking status",
        operation_description="Staff-only shortcut to confirm or cancel a booking.",
        request_body=BookingStatusUpdateSerializer,
        tags=["Bookings"],
    )
    @action(detail=True, methods=["patch"], permission_classes=[permissions.IsAdminUser])
    def status(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingStatusUpdateSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BookingSerializer(booking).data)

    @swagger_auto_schema(
        method="post",
        operation_summary="Check in to a booking",
        operation_description=(
            "Marks a booking as checked in. Only available once the booking's "
            "scheduled start time has arrived — checking in early is rejected. "
            "No request body — just put the booking ID in the URL path."
        ),
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        tags=["Bookings"],
    )
    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):
        booking = self.get_object()
        if booking.status not in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
            raise ValidationError(f"Cannot check in a booking with status '{booking.status}'.")

        start_datetime = timezone.make_aware(datetime.combine(booking.date, booking.start_time))
        if timezone.now() < start_datetime:
            raise ValidationError(
                "Check-in isn't open yet — it becomes available at the booking's start time."
            )

        booking.status = Booking.Status.CHECKED_IN
        booking.save()
        return Response(BookingSerializer(booking).data)

    @swagger_auto_schema(
        method="post",
        operation_summary="Check out and pay for a booking",
        operation_description=(
            "Marks a checked-in booking as checked out and records the payment "
            "(amount = space price per hour x booked duration)."
        ),
        request_body=CheckOutSerializer,
        tags=["Bookings"],
    )
    @action(detail=True, methods=["post"], url_path="check-out")
    def check_out(self, request, pk=None):
        booking = self.get_object()
        if booking.status != Booking.Status.CHECKED_IN:
            raise ValidationError(
                f"Cannot check out a booking with status '{booking.status}'. "
                "It must be checked in first."
            )

        payload = CheckOutSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        start = datetime.combine(booking.date, booking.start_time)
        end = datetime.combine(booking.date, booking.end_time)
        duration_hours = Decimal(str((end - start).total_seconds() / 3600))
        amount = (booking.space.price_per_hour * duration_hours).quantize(Decimal("0.01"))

        Payment.objects.create(
            booking=booking,
            method=payload.validated_data["payment_method"],
            amount=amount,
        )
        booking.status = Booking.Status.CHECKED_OUT
        booking.save()
        return Response(BookingSerializer(booking).data)


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    list: List all payment records for the authenticated user's bookings.
    retrieve: Get a single payment record.
    Staff users see every payment.
    """

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Payment.objects.none()
        user = self.request.user
        qs = Payment.objects.select_related("booking__space", "booking__user")
        if user.is_staff:
            return qs
        return qs.filter(booking__user=user)

    @swagger_auto_schema(operation_summary="List my payments", tags=["Payments"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve a payment", tags=["Payments"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
