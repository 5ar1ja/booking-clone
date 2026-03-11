from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "apartment",
        "check_in",
        "check_out",
        "status",
        "total_price",
        "created_at"
    )
    list_filter = (
        "status",
        "check_in",
        "check_out"
    )
    search_fields = (
        "tenant__email",
        "apartment__title"
    )
    readonly_fields = (
        "total_price",
        "created_at"
    )
