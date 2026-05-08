from datetime import date

from rest_framework import serializers

from .models import Booking

ERR_CHECKIN_PAST = 'check_in cannot be in the past'
ERR_CHECKOUT_BEFORE_CHECKIN = 'check_out must be after check_in'


class BookingSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Booking
        fields = ['status']
