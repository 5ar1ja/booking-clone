from datetime import date

from rest_framework import serializers
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

        if check_in and check_out:
            if check_in < date.today():
                raise serializers.ValidationError("check_in cannot be in the past")
            if check_in >= check_out:
                raise serializers.ValidationError("check_out must be after check_in")
        
        return data
    
class BookingStatusSerializer(serializers.ModelSerializer):
    # Needed only for changing status - used by apartment owner

    class Meta:
        model = Booking
        fields = ["status"]