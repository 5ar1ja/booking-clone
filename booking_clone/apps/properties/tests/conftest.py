import pytest
from rest_framework.test import APIClient
from apps.users.models import CustomUser
from apps.properties.models import Country, City, Apartment


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


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
def country(db) -> Country:
    return Country.objects.create(name='Kazakhstan')


@pytest.fixture
def city(db, country: Country) -> City:
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
