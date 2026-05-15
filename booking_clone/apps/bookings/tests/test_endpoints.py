import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from apps.bookings.models import Booking

BOOKING_LIST_URL = reverse('booking-list')

def get_booking_detail_url(pk):
    return reverse('booking-detail', kwargs={'pk': pk})

def get_booking_cancel_url(pk):
    return reverse('booking-cancel', kwargs={'pk': pk})

def get_booking_status_url(pk):
    return reverse('booking-update-status', kwargs={'pk': pk})

@pytest.mark.django_db
class TestBookingAPI:
    """Tests for Booking API endpoints."""

    # --- LIST ---
    def test_list_bookings_success(self, auth_client, renter, booking):
        """Good case: Tenant lists their bookings."""
        client = auth_client(renter)
        response = client.get(BOOKING_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_list_bookings_unauthenticated(self, api_client):
        """Bad case: Unauthenticated user lists bookings."""
        response = api_client.get(BOOKING_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_bookings_landlord_only_sees_own(self, auth_client, landlord, another_landlord, booking):
        """Bad case: Landlord should not see bookings of apartments they don't own."""
        client = auth_client(another_landlord)
        response = client.get(BOOKING_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    # --- CREATE ---
    def test_create_booking_success(self, auth_client, renter, apartment):
        """Good case: Renter creates a valid booking."""
        client = auth_client(renter)
        data = {
            'apartment': apartment.id,
            'check_in': date.today() + timedelta(days=5),
            'check_out': date.today() + timedelta(days=10)
        }
        response = client.post(BOOKING_LIST_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Booking.objects.count() == 1

    def test_create_booking_invalid_dates(self, auth_client, renter, apartment):
        """Bad case: Check-out before check-in."""
        client = auth_client(renter)
        data = {
            'apartment': apartment.id,
            'check_in': date.today() + timedelta(days=10),
            'check_out': date.today() + timedelta(days=5)
        }
        response = client.post(BOOKING_LIST_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_booking_past_date(self, auth_client, renter, apartment):
        """Bad case: Check-in in the past."""
        client = auth_client(renter)
        data = {
            'apartment': apartment.id,
            'check_in': date.today() - timedelta(days=5),
            'check_out': date.today() + timedelta(days=5)
        }
        response = client.post(BOOKING_LIST_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- RETRIEVE ---
    def test_retrieve_booking_success(self, auth_client, renter, booking):
        """Good case: Tenant retrieves their own booking."""
        client = auth_client(renter)
        response = client.get(get_booking_detail_url(booking.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == booking.id

    def test_retrieve_booking_not_found(self, auth_client, renter):
        """Bad case: Retrieve non-existent booking."""
        client = auth_client(renter)
        response = client.get(get_booking_detail_url(999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_booking_forbidden_other_renter(self, auth_client, another_renter, booking):
        """Bad case: Renter tries to retrieve someone else's booking."""
        client = auth_client(another_renter)
        response = client.get(get_booking_detail_url(booking.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- RESTRICTED ACTIONS ---
    def test_update_not_allowed(self, auth_client, renter, booking):
        """Bad case: Full update (PUT) is forbidden."""
        client = auth_client(renter)
        response = client.put(get_booking_detail_url(booking.id), {'status': 'confirmed'})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_partial_update_not_allowed(self, auth_client, renter, booking):
        """Bad case: Partial update (PATCH) is forbidden."""
        client = auth_client(renter)
        response = client.patch(get_booking_detail_url(booking.id), {'status': 'confirmed'})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, auth_client, renter, booking):
        """Bad case: Deletion (DELETE) is forbidden."""
        client = auth_client(renter)
        response = client.delete(get_booking_detail_url(booking.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # --- CANCEL ---
    def test_cancel_booking_success(self, auth_client, renter, booking):
        """Good case: Tenant cancels their own booking."""
        client = auth_client(renter)
        response = client.patch(get_booking_cancel_url(booking.id))
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CANCELLED

    def test_cancel_booking_unauthorized_landlord(self, auth_client, landlord, booking):
        """Bad case: Landlord tries to cancel tenant's booking via cancel action."""
        client = auth_client(landlord)
        response = client.patch(get_booking_cancel_url(booking.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cancel_already_cancelled(self, auth_client, renter, booking):
        """Bad case: Cancel a booking that is already cancelled."""
        booking.status = Booking.Status.CANCELLED
        booking.save()
        client = auth_client(renter)
        response = client.patch(get_booking_cancel_url(booking.id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- UPDATE STATUS ---
    def test_update_status_success(self, auth_client, landlord, booking):
        """Good case: Landlord accepts a booking."""
        client = auth_client(landlord)
        data = {'status': 'confirmed'}
        response = client.patch(get_booking_status_url(booking.id), data)
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

    def test_update_status_forbidden_tenant(self, auth_client, renter, booking):
        """Bad case: Tenant tries to update status."""
        client = auth_client(renter)
        data = {'status': 'confirmed'}
        response = client.patch(get_booking_status_url(booking.id), data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_status_invalid_value(self, auth_client, landlord, booking):
        """Bad case: Landlord provides invalid status value."""
        client = auth_client(landlord)
        data = {'status': 'invalid_status'}
        response = client.patch(get_booking_status_url(booking.id), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
