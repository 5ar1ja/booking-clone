# Django modules
from django.urls import reverse

# Third-party modules
import pytest
from rest_framework import status

# Project modules
from apps.users.models import CustomUser


@pytest.mark.django_db
class TestUserEndpoints:
    '''Test suite for user-related endpoints: register, login, profile.'''

    def test_register_user_success(self, api_client, user_data):
        '''Good case: Successfully register a new user.'''
        url = reverse('users-register')
        response = api_client.post(url, user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['email'] == user_data['email']
        assert CustomUser.objects.filter(email=user_data['email']).exists()

    def test_register_user_role_conflict(self, api_client, user_data):
        '''Bad case: Fail to register when both roles are selected.'''
        url = reverse('users-register')
        user_data['is_landlord'] = True
        user_data['is_renter'] = True
        response = api_client.post(url, user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_success(self, api_client, test_user):
        '''Good case: Successfully login with valid credentials.'''
        url = reverse('users-login')
        data = {
            'email': 'testuser@test.com',
            'password': 'testpass123'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_credentials(self, api_client, test_user):
        '''Bad case: Fail to login with wrong password.'''
        url = reverse('users-login')
        data = {
            'email': 'testuser@test.com',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_fetch_personal_info_success(self, api_client, test_user):
        '''Good case: Successfully fetch personal info when authenticated.'''
        api_client.force_authenticate(user=test_user)
        url = reverse('users-fetch-personal-info')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == test_user.email

    def test_fetch_personal_info_unauthenticated(self, api_client):
        '''Bad case: Fail to fetch personal info when not logged in.'''
        url = reverse('users-fetch-personal-info')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self, api_client, test_user):
        '''Good case: Successfully update user profile partially.'''
        api_client.force_authenticate(user=test_user)
        url = reverse('users-update-profile')
        data = {'first_name': 'UpdatedName'}
        response = api_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        assert test_user.first_name == 'UpdatedName'
