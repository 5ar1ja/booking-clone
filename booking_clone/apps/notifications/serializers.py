from rest_framework import serializers

from .models import Notification


ERR_MARK_READ_ONLY = 'Only marking notifications as read is supported.'


class NotificationReadSerializer(serializers.ModelSerializer):
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


class NotificationMarkReadSerializer(serializers.Serializer):
    is_read = serializers.BooleanField(default=True, required=False)

    def validate_is_read(self, value: bool) -> bool:
        if value is not True:
            raise serializers.ValidationError(ERR_MARK_READ_ONLY)
        return value


class NotificationMarkAllReadResponseSerializer(serializers.Serializer):
    updated = serializers.IntegerField()
