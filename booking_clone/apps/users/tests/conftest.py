import pytest
from rest_framework.test import APIClient
from apps.users.models import CustomUser

@pytest.fixture
def api_client():
    '''API client fixture for testing endpoints.'''
    return APIClient()

@pytest.fixture
def user_data():
    '''Valid user registration data.'''
    return {
        'email': 'newuser@test.com',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'is_landlord': True,
        'is_renter': False
    }

@pytest.fixture
def test_user(db):
    '''A saved user instance for testing login and profile.'''
    return CustomUser.objects.create_user(
        email='testuser@test.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        is_landlord=True,
        is_renter=False
    )
