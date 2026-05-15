from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from apps.notifications.models import Notification
from apps.notifications.utils import format_sse_event
from apps.notifications.views import _get_notifications_for_user

NOTIFICATION_LIST_URL = reverse('notification-list')


def get_notification_mark_read_url(pk: int) -> str:
    return reverse('notification-mark-read', kwargs={'pk': pk})


def get_booking_status_url(pk: int) -> str:
    return reverse('booking-update-status', kwargs={'pk': pk})


def get_booking_cancel_url(pk: int) -> str:
    return reverse('booking-cancel', kwargs={'pk': pk})


def run_on_commit_callbacks() -> None:
    from django.db import transaction

    for callback in transaction.get_connection().run_on_commit:
        callback[1]()


@pytest.mark.django_db
class TestNotificationEndpoints:
    def test_booking_create_notifies_landlord(self, auth_client, renter, apartment, landlord):
        client = auth_client(renter)

        response = client.post(
            reverse('booking-list'),
            {
                'apartment': apartment.id,
                'check_in': date.today() + timedelta(days=5),
                'check_out': date.today() + timedelta(days=8),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        run_on_commit_callbacks()
        notification = Notification.objects.get(user=landlord)
        assert notification.event_type == Notification.EventType.BOOKING_CREATED
        assert notification.booking_id == response.data['id']
        assert notification.metadata['status'] == 'pending'

    def test_booking_status_update_notifies_renter(self, auth_client, landlord, renter, booking):
        client = auth_client(landlord)

        response = client.patch(get_booking_status_url(booking.id), {'status': 'cancelled'})

        assert response.status_code == status.HTTP_200_OK
        run_on_commit_callbacks()
        notification = Notification.objects.get(user=renter)
        assert notification.event_type == Notification.EventType.BOOKING_STATUS_CHANGED
        assert notification.booking_id == booking.id
        assert notification.metadata['previous_status'] == 'pending'
        assert notification.metadata['status'] == 'cancelled'

    def test_booking_cancel_notifies_landlord(self, auth_client, renter, landlord, booking):
        client = auth_client(renter)

        response = client.patch(get_booking_cancel_url(booking.id))

        assert response.status_code == status.HTTP_200_OK
        run_on_commit_callbacks()
        notification = Notification.objects.get(user=landlord)
        assert notification.event_type == Notification.EventType.BOOKING_CANCELLED
        assert notification.booking_id == booking.id
        assert notification.metadata['status'] == 'cancelled'

    def test_notification_list_only_returns_current_user_notifications(
        self,
        auth_client,
        landlord,
        renter,
        another_user,
        booking,
    ):
        Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CREATED,
            message='For landlord',
        )
        Notification.objects.create(
            user=another_user,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CREATED,
            message='For another user',
        )

        client = auth_client(landlord)
        response = client.get(NOTIFICATION_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['message'] == 'For landlord'

    def test_notification_list_filters_by_read_status(
        self,
        auth_client,
        landlord,
        booking,
    ):
        Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CREATED,
            message='Unread',
        )
        Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CANCELLED,
            message='Read',
            is_read=True,
        )

        client = auth_client(landlord)
        response = client.get(NOTIFICATION_LIST_URL, {'is_read': 'false'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['message'] == 'Unread'

    def test_mark_notification_read(self, auth_client, landlord, booking):
        notification = Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CREATED,
            message='Unread message',
        )

        client = auth_client(landlord)
        response = client.patch(get_notification_mark_read_url(notification.id))

        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_notifications_read(self, auth_client, landlord, booking):
        Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CREATED,
            message='First',
        )
        Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CANCELLED,
            message='Second',
        )

        client = auth_client(landlord)
        response = client.patch(reverse('notification-mark-all-read'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated'] == 2
        assert Notification.objects.filter(user=landlord, is_read=False).count() == 0

    def test_sse_replay_query_returns_only_newer_notifications(
        self,
        landlord,
        booking,
    ):
        first_notification = Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CREATED,
            message='First',
        )
        second_notification = Notification.objects.create(
            user=landlord,
            booking=booking,
            event_type=Notification.EventType.BOOKING_CANCELLED,
            message='Second',
        )

        notifications = _get_notifications_for_user(
            landlord.id,
            after_id=first_notification.id,
        )
        replayed_event = format_sse_event(second_notification)

        assert [notification.id for notification in notifications] == [second_notification.id]
        assert f'id: {second_notification.id}' in replayed_event
        assert 'event: booking_cancelled' in replayed_event
        assert '"message": "Second"' in replayed_event

    def test_invalid_status_update_is_rejected(self, auth_client, landlord, booking):
        client = auth_client(landlord)

        response = client.patch(get_booking_status_url(booking.id), {'status': 'completed'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'][0] == 'status must be either confirmed or cancelled'
