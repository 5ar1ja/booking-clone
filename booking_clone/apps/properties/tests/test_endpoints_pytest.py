import pytest

from apps.properties.models import Apartment
from django.urls import reverse

from rest_framework import status


@pytest.mark.django_db
class TestApartmentEndpoints:
    
    # --- LIST ---
    def test_list_apartments_success(self, api_client, apartment):
        url = reverse('apartment-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == apartment.title

    def test_list_apartments_invalid_method(self, api_client, landlord):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-list')
        # DELETE is not allowed on the list endpoint
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_list_apartments_invalid_filter_type(self, api_client, apartment):
        url = reverse('apartment-list')
        # Passing a string to an integer filter (rooms)
        response = api_client.get(url, {'rooms': 'abc'})
        # This project's configuration seems to return 400 for invalid filter types
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- CREATE ---
    def test_create_apartment_success(self, api_client, landlord, city):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-list')
        data = {
            'title': 'New Apt',
            'description': 'Desc',
            'address': 'Addr',
            'city_id': city.id,
            'price_per_night': '100.00',
            'rooms': 2
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Apartment.objects.filter(title='New Apt').exists()

    def test_create_apartment_forbidden_for_renter(self, api_client, renter, city):
        api_client.force_authenticate(user=renter)
        url = reverse('apartment-list')
        data = {
            'title': 'Renter Apt',
            'description': 'Desc',
            'address': 'Addr',
            'city_id': city.id,
            'price_per_night': '100.00',
            'rooms': 2
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_apartment_invalid_data(self, api_client, landlord, city):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-list')
        data = {
            'title': '', # Invalid: blank
            'description': 'Desc',
            'address': 'Addr',
            'city_id': city.id,
            'price_per_night': -10, # Invalid: negative
            'rooms': 0 # Invalid: min is 1
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- RETRIEVE ---
    def test_retrieve_apartment_success(self, api_client, apartment):
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == apartment.title

    def test_retrieve_apartment_not_found(self, api_client):
        url = reverse('apartment-detail', kwargs={'pk': 9999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_apartment_invalid_method(self, api_client, landlord):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': 1}) # Any ID
        # POST is not allowed on detail endpoint
        response = api_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # --- UPDATE (PUT) ---
    def test_update_apartment_success(self, api_client, landlord, apartment, city):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        data = {
            'title': 'Updated Title',
            'description': apartment.description,
            'address': apartment.address,
            'city_id': city.id,
            'price_per_night': '150.00',
            'rooms': 3
        }
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        apartment.refresh_from_db()
        assert apartment.title == 'Updated Title'

    def test_update_apartment_not_owner(self, api_client, another_landlord, apartment, city):
        api_client.force_authenticate(user=another_landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        data = {
            'title': 'Hack',
            'description': 'Hack',
            'address': 'Hack',
            'city_id': city.id,
            'price_per_night': '200.00',
            'rooms': 5
        }
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_apartment_invalid_data(self, api_client, landlord, apartment):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        data = {
            'title': 'New',
            'price_per_night': 'abc' # Invalid
        }
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- PARTIAL UPDATE (PATCH) ---
    def test_patch_apartment_success(self, api_client, landlord, apartment):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        data = {'title': 'Patched Title'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        apartment.refresh_from_db()
        assert apartment.title == 'Patched Title'

    def test_patch_apartment_forbidden_for_renter(self, api_client, renter, apartment):
        api_client.force_authenticate(user=renter)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        data = {'title': 'Renter Patch'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_apartment_invalid_data(self, api_client, landlord, apartment):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        data = {'price_per_night': -50}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- DELETE ---
    def test_delete_apartment_success(self, api_client, landlord, apartment):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Apartment.objects.filter(pk=apartment.pk).exists()

    def test_delete_apartment_not_owner(self, api_client, another_landlord, apartment):
        api_client.force_authenticate(user=another_landlord)
        url = reverse('apartment-detail', kwargs={'pk': apartment.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Apartment.objects.filter(pk=apartment.pk).exists()

    def test_delete_apartment_not_found(self, api_client, landlord):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-detail', kwargs={'pk': 9999})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- REVIEWS ACTION ---
    def test_apartment_reviews_success(self, api_client, apartment):
        url = reverse('apartment-reviews', kwargs={'pk': apartment.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data['results'], list)

    def test_apartment_reviews_not_found(self, api_client):
        url = reverse('apartment-reviews', kwargs={'pk': 9999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_apartment_reviews_invalid_method(self, api_client, landlord, apartment):
        api_client.force_authenticate(user=landlord)
        url = reverse('apartment-reviews', kwargs={'pk': apartment.pk})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
