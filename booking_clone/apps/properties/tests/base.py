from rest_framework.test import APITestCase, APIClient

from apps.users.models import CustomUser
from apps.properties.models import City, Apartment, Country


class BaseApartmentTest(APITestCase):

    def setUp(self):

        self.client = APIClient()

        self.landlord = CustomUser.objects.create_user(
            email="landlord@test.com",
            password="testpass123",
            is_landlord=True
        )

        self.renter = CustomUser.objects.create_user(
            email="renter@test.com",
            password="testpass123",
            is_renter=True
        )

        # Countries
        self.kazakhstan = Country.objects.create(name="Kazakhstan")

        # Cities
        self.almaty = City.objects.create(name="Almaty", country=self.kazakhstan)
        self.astana = City.objects.create(name="Astana", country=self.kazakhstan)
        

        # Apartment 1: Almaty, Price 500, Rooms 2
        self.apt1 = Apartment.objects.create(
            title="Almaty Central",
            description="Test Decription",
            address="Test Address 1",
            city=self.almaty,
            price_per_night=500,
            rooms=2,
            owner=self.landlord
        )

        # Apartment 2: Almaty, Price 300, Rooms 1
        self.apt2 = Apartment.objects.create(
            title="Almaty Budget",
            description="Test Description",
            address="Test Address 2",
            city=self.almaty,
            price_per_night=300,
            rooms=1,
            owner=self.landlord
        )

        # Apartment 3: Astana, Price 700, Rooms 3
        self.apt3 = Apartment.objects.create(
            title="Astana Luxury",
            description="Test Description",
            address="Test Address 3",
            city=self.astana,
            price_per_night=700,
            rooms=3,
            owner=self.landlord
        )