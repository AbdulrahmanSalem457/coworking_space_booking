from django.contrib import admin

from .models import Booking, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["space", "user", "date", "start_time", "end_time", "status"]
    list_filter = ["status", "date"]
    search_fields = ["space__name", "user__username"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["booking", "method", "amount", "paid_at"]
    list_filter = ["method"]
    search_fields = ["booking__space__name", "booking__user__username"]
