import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.users.models import CustomUser

AVATAR_FILENAME = 'avatar.gif'
AVATAR_CONTENT_TYPE = 'image/gif'
AVATAR_UPLOAD_PREFIX = 'avatars/'
TEST_AVATAR_IMAGE = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
    b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


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
        assert 'avatar' in response.data

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

    def test_update_profile_avatar_success(
        self,
        api_client,
        test_user,
        settings,
        tmp_path,
    ):
        '''Good case: Successfully upload an avatar with profile update.'''
        settings.MEDIA_ROOT = tmp_path
        api_client.force_authenticate(user=test_user)
        url = reverse('users-update-profile')
        avatar = SimpleUploadedFile(
            AVATAR_FILENAME,
            TEST_AVATAR_IMAGE,
            content_type=AVATAR_CONTENT_TYPE,
        )

        response = api_client.patch(url, {'avatar': avatar}, format='multipart')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['avatar']
        test_user.refresh_from_db()
        assert test_user.avatar.name.startswith(AVATAR_UPLOAD_PREFIX)
