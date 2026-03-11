from rest_framework import status
from .base import BaseApartmentTest


class ApartmentPermissionTests(BaseApartmentTest):

    def test_owner_can_update_apartment(self):

        self.client.force_authenticate(user=self.landlord)

        response = self.client.patch(
            f"/properties/apartments/{self.apt1.id}/",
            {"title": "Updated Title"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_owner_cannot_update(self):

        self.client.force_authenticate(user=self.renter)

        response = self.client.patch(
            f"/properties/apartments/{self.apt1.id}/",
            {"title": "Hack"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)