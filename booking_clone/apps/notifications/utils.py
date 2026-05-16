from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import CustomUser
from .models import Notification

if TYPE_CHECKING:
    from apps.bookings.models import Booking


def create_notification(
    *,
    user: CustomUser,
    event_type: str,
    message: str,
    booking: Booking | None = None,
    metadata: dict[str, Any] | None = None,
) -> Notification:
    '''Creates a durable notification row after the surrounding transaction commits.'''

    return Notification.objects.create(
        user=user,
        booking=booking,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


def notify_after_commit(
    *,
    user: CustomUser,
    event_type: str,
    message: str,
    booking: Booking | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    '''Defers notification creation until the current transaction commits successfully.'''

    transaction.on_commit(
        lambda: create_notification(
            user=user,
            event_type=event_type,
            message=message,
            booking=booking,
            metadata=metadata,
        )
    )


def serialize_notification(notification: Notification) -> dict[str, Any]:
    '''Builds the structured payload sent via the API and SSE stream.'''

    return {
        'id': notification.id,
        'event_type': notification.event_type,
        'message': notification.message,
        'booking_id': notification.booking_id,
        'metadata': notification.metadata,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat(),
    }


def format_sse_event(notification: Notification) -> str:
    '''Formats a notification as a replayable SSE event.'''

    payload = json.dumps(serialize_notification(notification))
    return (
        f'id: {notification.id}\n'
        f'event: {notification.event_type}\n'
        f'data: {payload}\n\n'
    )


def get_user_from_jwt(token: str) -> CustomUser | None:
    '''
    Helper to authenticate user from JWT token manually.
    Useful for async views where standard middleware might be tricky.
    '''
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        return CustomUser.objects.get(id=user_id)
    except Exception:
        return None
