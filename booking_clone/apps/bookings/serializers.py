from datetime import date

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Booking

ERR_CHECKIN_PAST = _('check_in cannot be in the past')
ERR_CHECKOUT_BEFORE_CHECKIN = _('check_out must be after check_in')
ERR_INVALID_STATUS = _('status must be either confirmed or cancelled')


class BookingReadSerializer(serializers.ModelSerializer):
    tenant = serializers.ReadOnlyField(source='tenant.email')
    apartment_title = serializers.ReadOnlyField(source='apartment.title')

    class Meta:
        model = Booking
        fields = [
            'id',
            'tenant',
            'apartment',
            'apartment_title',
            'check_in',
            'check_out',
            'status',
            'total_price',
            'created_at',
        ]
        read_only_fields = ['tenant', 'status', 'total_price', 'created_at']


class BookingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'apartment',
            'check_in',
            'check_out',
        ]

    def validate(self, data: dict) -> dict:
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if check_in and check_out:
            if check_in < date.today():
                raise serializers.ValidationError(ERR_CHECKIN_PAST)
            if check_in >= check_out:
                raise serializers.ValidationError(ERR_CHECKOUT_BEFORE_CHECKIN)

        return data


class BookingStatusSerializer(serializers.ModelSerializer):
    '''Used by the apartment owner to accept or reject a booking.'''

    def validate_status(self, value: str) -> str:
        allowed_statuses = {
            Booking.Status.CONFIRMED,
            Booking.Status.CANCELLED,
        }
        if value not in allowed_statuses:
            raise serializers.ValidationError(ERR_INVALID_STATUS)
        return value

    class Meta:
        model = Booking
        fields = ['status']
