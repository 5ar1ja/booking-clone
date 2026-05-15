from datetime import date

from django.db import transaction
from rest_framework import serializers

from apps.properties.models import Apartment
from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    tenant = serializers.ReadOnlyField(source="tenant.email")
    apartment_title = serializers.ReadOnlyField(source="apartment.title")

    class Meta:
        model = Booking
        fields = [
            "id",
            "tenant",
            "apartment",
            "apartment_title",
            "check_in",
            "check_out",
            "status",
            "total_price",
            "created_at",
        ]
        read_only_fields = ["tenant", "status", "total_price", "created_at"]

    def validate(self, data):
        check_in = data.get("check_in")
        check_out = data.get("check_out")
        apartment = data.get("apartment")

        if check_in and check_out:
            if check_in < date.today():
                raise serializers.ValidationError("check_in cannot be in the past")
            if check_in >= check_out:
                raise serializers.ValidationError("check_out must be after check_in")

        # Check for overlapping dates and use pessimistic locking to prevent race conditions
        if apartment and check_in and check_out:
            with transaction.atomic():
                # Lock the apartment row for the duration of this transaction
                Apartment.objects.select_for_update().get(id=apartment.id)

                overlapping_bookings = Booking.objects.filter(
                    apartment=apartment,
                    status__in=[Booking.Status.PENDING, Booking.Status.ACCEPTED],
                    check_in__lt=check_out,
                    check_out__gt=check_in
                ).exists()

                if overlapping_bookings:
                    raise serializers.ValidationError("This apartment is already booked for these dates.")
        
        return data
    
class BookingStatusSerializer(serializers.ModelSerializer):
    # Needed only for changing status - used by apartment owner

    class Meta:
        model = Booking
        fields = ["status"]