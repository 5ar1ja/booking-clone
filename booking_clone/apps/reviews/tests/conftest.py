import pytest
from apps.bookings.models import Booking
from apps.reviews.models import Review
from datetime import date, timedelta

# Import fixtures from properties tests
from apps.properties.tests.conftest import (
    api_client, 
    landlord, 
    another_landlord, 
    renter, 
    country, 
    city, 
    apartment
)

@pytest.fixture
def completed_booking(db, renter, apartment):
    return Booking.objects.create(
        tenant=renter,
        apartment=apartment,
        check_in=date.today() - timedelta(days=5),
        check_out=date.today() - timedelta(days=2),
        status=Booking.Status.COMPLETED
    )

@pytest.fixture
def pending_booking(db, renter, apartment):
    return Booking.objects.create(
        tenant=renter,
        apartment=apartment,
        check_in=date.today() + timedelta(days=1),
        check_out=date.today() + timedelta(days=4),
        status=Booking.Status.PENDING
    )

@pytest.fixture
def review(db, renter, apartment, completed_booking):
    return Review.objects.create(
        apartment=apartment,
        author=renter,
        rating=5,
        comment="Amazing stay!"
    )
