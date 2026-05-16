# Third-party modules
from rest_framework import serializers

# Project modules
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'event_type',
            'message',
            'metadata',
            'booking_id',
            'is_read',
            'created_at',
        ]
        read_only_fields = fields
