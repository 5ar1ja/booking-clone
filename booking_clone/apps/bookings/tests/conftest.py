# Python modules
from typing import Callable

# Third-party modules
import pytest
from rest_framework.test import APIClient

# Project modules
from apps.bookings.models import Booking
from apps.properties.models import Country, City, Apartment
from apps.users.models import CustomUser


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_client(api_client: APIClient) -> Callable[[CustomUser], APIClient]:
    def _auth_client(user):
        api_client.force_authenticate(user=user)
        return api_client
    return _auth_client


@pytest.fixture
def landlord(db) -> CustomUser:
    return CustomUser.objects.create_user(
        email='landlord@test.com',
        password='testpass123',
        is_landlord=True,
    )


@pytest.fixture
def another_landlord(db) -> CustomUser:
    return CustomUser.objects.create_user(
        email='another_landlord@test.com',
        password='testpass123',
        is_landlord=True,
    )


@pytest.fixture
def renter(db) -> CustomUser:
    return CustomUser.objects.create_user(
        email='renter@test.com',
        password='testpass123',
        is_renter=True,
    )


@pytest.fixture
def another_renter(db) -> CustomUser:
    return CustomUser.objects.create_user(
        email='another_renter@test.com',
        password='testpass123',
        is_renter=True,
    )


@pytest.fixture
def country(db) -> Country:
    return Country.objects.create(name='Kazakhstan')


@pytest.fixture
def city(db, country) -> City:
    return City.objects.create(name='Almaty', country=country)


@pytest.fixture
def apartment(db, landlord: CustomUser, city: City) -> Apartment:
    return Apartment.objects.create(
        title='Almaty Central',
        description='Test Description',
        address='Test Address 1',
        city=city,
        price_per_night=500,
        rooms=2,
        owner=landlord,
    )


@pytest.fixture
def booking(db, renter: CustomUser, apartment: Apartment) -> Booking:
    from datetime import date, timedelta
    return Booking.objects.create(
        tenant=renter,
        apartment=apartment,
        check_in=date.today() + timedelta(days=1),
        check_out=date.today() + timedelta(days=3),
        status=Booking.Status.PENDING
    )
