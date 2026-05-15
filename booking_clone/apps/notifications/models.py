from django.conf import settings
from django.db import models


class Notification(models.Model):
    '''Stores durable user notifications for API access and SSE replay.'''

    class EventType(models.TextChoices):
        BOOKING_CREATED = 'booking_created', 'Booking created'
        BOOKING_STATUS_CHANGED = 'booking_status_changed', 'Booking status changed'
        BOOKING_CANCELLED = 'booking_cancelled', 'Booking cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Recipient',
        help_text='The user who will receive this notification.',
    )
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Booking',
        help_text='The booking related to this notification, when applicable.',
    )
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        verbose_name='Event type',
        help_text='Machine-readable notification event type.',
    )
    message = models.TextField(
        verbose_name='Message',
        help_text='Human-readable notification message.',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadata',
        help_text='Structured event payload for clients.',
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Is read',
        help_text='Whether the user has seen this notification.',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
        help_text='When the notification was generated.',
    )

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-id']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f'Notification #{self.id} for {self.user.email}'
