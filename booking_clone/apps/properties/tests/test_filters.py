from rest_framework import status
from apps.properties.models import Apartment, City
from .base import BaseApartmentTest


class ApartmentFilterTests(BaseApartmentTest):

    def test_filter_by_country(self):
        
        response = self.client.get(f"/properties/apartments/?country={self.kazakhstan.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)


    def test_filter_by_city(self):

        response = self.client.get(f"/properties/apartments/?city={self.almaty.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data), 2) # should find 2 Almaty not Astana


    def test_filter_by_min_price(self):

        response = self.client.get("/properties/apartments/?min_price=400")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    
    def test_filter_by_max_price(self):

        response = self.client.get("/properties/apartments/?max_price=500")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


    def test_filter_by_rooms(self):

        response = self.client.get("/properties/apartments/?rooms=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


    def test_filter_combination(self):
        # Almaty + Price < 400
        params = {
            'city': self.almaty.id,
            'max_price': 400
        }
        response = self.client.get("/properties/apartments/", params)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Almaty Budget")