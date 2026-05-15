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
    """tests for api endpoints"""
    def test_list_bookings_success(self, auth_client, renter, booking):
        """good case: tenant lists their bookings"""
        client = auth_client(renter)
        response = client.get(BOOKING_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_list_bookings_unauthenticated(self, api_client):
        """bad case: unauthenticated user lists bookings"""
        response = api_client.get(BOOKING_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_bookings_landlord_only_sees_own(self, auth_client, landlord, another_landlord, booking):
        """bad case: landlord shouldnt see bookings of apartments they dont own"""
        client = auth_client(another_landlord)
        response = client.get(BOOKING_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_list_bookings_filter_by_status(self, auth_client, renter, booking):
        """good case: tenant filters bookings by status"""
        client = auth_client(renter)
        response = client.get(BOOKING_LIST_URL, {'status': Booking.Status.PENDING})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == Booking.Status.PENDING

    # --- CREATE ---
    def test_create_booking_success(self, auth_client, renter, apartment):
        """good case: renter creates a valid booking"""
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
        """bad case: check-out before check-in"""
        client = auth_client(renter)
        data = {
            'apartment': apartment.id,
            'check_in': date.today() + timedelta(days=10),
            'check_out': date.today() + timedelta(days=5)
        }
        response = client.post(BOOKING_LIST_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_booking_past_date(self, auth_client, renter, apartment):
        """bad case: check-in in the past"""
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
        """good case: tenant retrieves their own booking"""
        client = auth_client(renter)
        response = client.get(get_booking_detail_url(booking.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == booking.id

    def test_retrieve_booking_not_found(self, auth_client, renter):
        """bad case: retrieve non-existent booking"""
        client = auth_client(renter)
        response = client.get(get_booking_detail_url(999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_booking_forbidden_other_renter(self, auth_client, another_renter, booking):
        """bad case: renter tries to retrieve someone else's booking"""
        client = auth_client(another_renter)
        response = client.get(get_booking_detail_url(booking.id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- RESTRICTED ACTIONS ---
    def test_update_not_allowed(self, auth_client, renter, booking):
        """bad case: PUT is forbidden"""
        client = auth_client(renter)
        response = client.put(get_booking_detail_url(booking.id), {'status': 'confirmed'})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_partial_update_not_allowed(self, auth_client, renter, booking):
        """bad case: PATCH is forbidden"""
        client = auth_client(renter)
        response = client.patch(get_booking_detail_url(booking.id), {'status': 'confirmed'})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, auth_client, renter, booking):
        """bad case: DELETE is forbidden"""
        client = auth_client(renter)
        response = client.delete(get_booking_detail_url(booking.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # --- CANCEL ---
    def test_cancel_booking_success(self, auth_client, renter, booking):
        """good case: tenant cancels their own booking"""
        client = auth_client(renter)
        response = client.patch(get_booking_cancel_url(booking.id))
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CANCELLED

    def test_cancel_booking_unauthorized_landlord(self, auth_client, landlord, booking):
        """bad case: landlord tries to cancel tenants booking cherez cancel action"""
        client = auth_client(landlord)
        response = client.patch(get_booking_cancel_url(booking.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cancel_already_cancelled(self, auth_client, renter, booking):
        """bad case: cancel a booking that is already cancelled"""
        booking.status = Booking.Status.CANCELLED
        booking.save()
        client = auth_client(renter)
        response = client.patch(get_booking_cancel_url(booking.id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- UPDATE STATUS ---
    def test_update_status_success(self, auth_client, landlord, booking):
        """good case: landlord accepts booking"""
        client = auth_client(landlord)
        data = {'status': 'confirmed'}
        response = client.patch(get_booking_status_url(booking.id), data)
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

    def test_update_status_forbidden_tenant(self, auth_client, renter, booking):
        """bad case: tenant tries to update status"""
        client = auth_client(renter)
        data = {'status': 'confirmed'}
        response = client.patch(get_booking_status_url(booking.id), data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_status_invalid_value(self, auth_client, landlord, booking):
        """bad case: landlord provides invalid status value"""
        client = auth_client(landlord)
        data = {'status': 'invalid_status'}
        response = client.patch(get_booking_status_url(booking.id), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_status_confirmed_triggers_email(self, auth_client, landlord, booking, mocker):
        """good case: confirming a booking triggers the background email task"""

        mock_task = mocker.patch('apps.bookings.tasks.send_booking_confirmation_email.delay')
        
        client = auth_client(landlord)
        data = {'status': 'confirmed'}
        
        response = client.patch(get_booking_status_url(booking.id), data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # manually trigger callbacks for tje test
        from django.db import transaction
        for callback in transaction.get_connection().run_on_commit:
            callback[1]()
            
        assert mock_task.called
        assert mock_task.call_args[0][0] == booking.id
