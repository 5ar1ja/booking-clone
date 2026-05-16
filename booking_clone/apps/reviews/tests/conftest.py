# Python modules
from datetime import date, timedelta

# Third-party modules
import pytest

# Project modules
from apps.bookings.models import Booking
from apps.properties.models import Apartment
from apps.properties.tests.conftest import (
    api_client,
    landlord,
    another_landlord,
    renter,
    country,
    city,
    apartment,
)
from apps.reviews.models import Review
from apps.users.models import CustomUser


@pytest.fixture
def completed_booking(db, renter: CustomUser, apartment: Apartment) -> Booking:
    return Booking.objects.create(
        tenant=renter,
        apartment=apartment,
        check_in=date.today() - timedelta(days=5),
        check_out=date.today() - timedelta(days=2),
        status=Booking.Status.COMPLETED
    )


@pytest.fixture
def pending_booking(db, renter: CustomUser, apartment: Apartment) -> Booking:
    return Booking.objects.create(
        tenant=renter,
        apartment=apartment,
        check_in=date.today() + timedelta(days=1),
        check_out=date.today() + timedelta(days=4),
        status=Booking.Status.PENDING
    )


@pytest.fixture
def review(db, renter: CustomUser, apartment: Apartment, completed_booking: Booking) -> Review:
    return Review.objects.create(
        apartment=apartment,
        author=renter,
        rating=5,
        comment="Amazing stay!"
    )
