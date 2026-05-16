from datetime import date, timedelta
from rest_framework import status
from apps.bookings.models import Booking
from .base import BaseApartmentTest


class ApartmentFilterTests(BaseApartmentTest):

    def test_filter_by_country(self):
        """Good case: Filter apartments by country ID."""
        response = self.client.get(
            f'/properties/apartments/?country={self.kazakhstan.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_filter_by_city(self):
        """Good case: Filter apartments by city ID."""
        response = self.client.get(
            f'/properties/apartments/?city={self.almaty.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(len(response.data['results']), 2)  # 2 Almaty, not Astana

    def test_filter_by_min_price(self):
        """Good case: Filter apartments by minimum price."""
        response = self.client.get('/properties/apartments/?min_price=400')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_by_max_price(self):
        """Good case: Filter apartments by maximum price."""
        response = self.client.get('/properties/apartments/?max_price=500')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_by_rooms(self):
        """Good case: Filter apartments by number of rooms."""
        response = self.client.get('/properties/apartments/?rooms=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_combination(self):
        """Good case: Filter apartments using a combination of city and max price."""
        # Almaty + Price < 400
        params = {
            'city': self.almaty.id,
            'max_price': 400
        }
        response = self.client.get('/properties/apartments/', params)

        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Almaty Budget')

    def test_filter_by_availability_success(self):
        """Good case: Filter for available apartments in a free date range."""
        check_in = date.today() + timedelta(days=10)
        check_out = date.today() + timedelta(days=15)
        
        # Create a booking for apt1 in a DIFFERENT range
        Booking.objects.create(
            tenant=self.renter,
            apartment=self.apt1,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=5),
            status=Booking.Status.CONFIRMED
        )

        params = {
            'check_in': check_in,
            'check_out': check_out
        }
        response = self.client.get('/properties/apartments/', params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All 3 apartments should be available
        self.assertEqual(len(response.data['results']), 3)

    def test_filter_by_availability_exclude_booked(self):
        """Bad case: Exclude apartments that are already booked during the requested range."""
        check_in = date.today() + timedelta(days=5)
        check_out = date.today() + timedelta(days=10)
        
        # Book apt1 exactly on these dates
        Booking.objects.create(
            tenant=self.renter,
            apartment=self.apt1,
            check_in=check_in,
            check_out=check_out,
            status=Booking.Status.CONFIRMED
        )
        
        # Book apt2 overlapping these dates
        Booking.objects.create(
            tenant=self.renter,
            apartment=self.apt2,
            check_in=check_in - timedelta(days=2),
            check_out=check_in + timedelta(days=2),
            status=Booking.Status.PENDING
        )

        params = {
            'check_in': check_in,
            'check_out': check_out
        }
        response = self.client.get('/properties/apartments/', params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # apt1 and apt2 are busy, only apt3 remains
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.apt3.id)
