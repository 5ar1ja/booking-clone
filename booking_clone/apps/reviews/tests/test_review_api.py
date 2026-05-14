import pytest
from django.urls import reverse
from rest_framework import status
from apps.reviews.models import Review

@pytest.mark.django_db
class TestReviewAPI:
    
    # --- LIST ---
    def test_list_reviews_success(self, api_client, review):
        url = reverse('review-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_reviews_filter_by_apartment(self, api_client, review):
        url = reverse('review-list')
        response = api_client.get(url, {'apartment': review.apartment.id})
        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]['apartment'] == review.apartment.id

    def test_list_reviews_filter_invalid_apartment(self, api_client, review):
        # django-filter validates if the ID exists in the queryset of the model
        url = reverse('review-list')
        response = api_client.get(url, {'apartment': 999})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- CREATE ---
    def test_create_review_success(self, api_client, renter, apartment, completed_booking):
        api_client.force_authenticate(user=renter)
        url = reverse('review-list')
        data = {'apartment': apartment.id, 'rating': 4, 'comment': 'Great place!'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Review.objects.count() == 1 

    def test_create_review_fail_not_stayed(self, api_client, renter, apartment):
        api_client.force_authenticate(user=renter)
        url = reverse('review-list')
        data = {'apartment': apartment.id, 'rating': 4, 'comment': 'Great place!'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'stayed' in response.data['detail'].lower()

    def test_create_review_fail_own_apartment(self, api_client, landlord, apartment):
        api_client.force_authenticate(user=landlord)
        url = reverse('review-list')
        data = {'apartment': apartment.id, 'rating': 5, 'comment': 'I love my own place!'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'own' in response.data['detail'].lower()

    # --- RETRIEVE ---
    def test_retrieve_review_success(self, api_client, review):
        url = reverse('review-detail', kwargs={'pk': review.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['comment'] == review.comment

    def test_retrieve_review_not_found(self, api_client):
        url = reverse('review-detail', kwargs={'pk': 999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_review_invalid_pk(self, api_client):
        url = "/api/reviews/abc/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- UPDATE ---
    def test_update_review_success(self, api_client, renter, review):
        api_client.force_authenticate(user=renter)
        url = reverse('review-detail', kwargs={'pk': review.id})
        data = {'apartment': review.apartment.id, 'rating': 3, 'comment': 'Updated comment'}
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.rating == 3

    def test_update_review_fail_not_author(self, api_client, another_landlord, review):
        api_client.force_authenticate(user=another_landlord)
        url = reverse('review-detail', kwargs={'pk': review.id})
        data = {'apartment': review.apartment.id, 'rating': 1, 'comment': 'Sabotage!'}
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_review_fail_invalid_rating(self, api_client, renter, review):
        api_client.force_authenticate(user=renter)
        url = reverse('review-detail', kwargs={'pk': review.id})
        data = {'apartment': review.apartment.id, 'rating': 6, 'comment': 'Too high!'}
        response = api_client.put(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- PARTIAL UPDATE ---
    def test_partial_update_review_success(self, api_client, renter, review):
        api_client.force_authenticate(user=renter)
        url = reverse('review-detail', kwargs={'pk': review.id})
        data = {'rating': 2}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.rating == 2

    def test_partial_update_review_fail_not_authenticated(self, api_client, review):
        url = reverse('review-detail', kwargs={'pk': review.id})
        data = {'rating': 2}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_partial_update_review_fail_readonly_author(self, api_client, renter, review):
        api_client.force_authenticate(user=renter)
        url = reverse('review-detail', kwargs={'pk': review.id})
        data = {'author': 'hacker@test.com'}
        response = api_client.patch(url, data)
        # Author is ReadOnlyField in ReviewReadSerializer, but ignored in WriteSerializer
        review.refresh_from_db()
        assert review.author.email == 'renter@test.com'

    # --- DESTROY ---
    def test_delete_review_success(self, api_client, renter, review):
        api_client.force_authenticate(user=renter)
        url = reverse('review-detail', kwargs={'pk': review.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Review.objects.count() == 0

    def test_delete_review_fail_not_author(self, api_client, another_landlord, review):
        api_client.force_authenticate(user=another_landlord)
        url = reverse('review-detail', kwargs={'pk': review.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Review.objects.count() == 1

    def test_delete_review_fail_not_authenticated(self, api_client, review):
        url = reverse('review-detail', kwargs={'pk': review.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Review.objects.count() == 1
