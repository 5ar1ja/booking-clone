from rest_framework import status
from apps.properties.models import Apartment
from .base import BaseApartmentTest


class ApartmentAPITests(BaseApartmentTest):

    def test_list_apartments(self):

        response = self.client.get("/properties/apartments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_landlord_can_create_apartment(self):

        self.client.force_authenticate(user=self.landlord)

        data = {
            "title": "New Apartment",
            "description": "Nice place",
            "address": "Street 5",
            "city_id": self.almaty.id,
            "price_per_night": 600,
            "rooms": 3
        }

        response = self.client.post("/properties/apartments/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Apartment.objects.count(), 4) # 3 from base + 1 here

    def test_renter_cannot_create_apartment(self):

        self.client.force_authenticate(user=self.renter)

        data = {
            "title": "Illegal Apartment",
            "description": "Should fail",
            "address": "Street 10",
            "city_id": self.almaty.id,
            "price_per_night": 400,
            "rooms": 2
        }

        response = self.client.post("/properties/apartments/", data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)