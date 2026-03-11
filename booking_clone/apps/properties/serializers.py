from rest_framework import serializers
from .models import Apartment, City, Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]


class CitySerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        source="country",
        write_only=True
    )

    class Meta:
        model = City
        fields = ["id", "name", "country", "country_id"]


class ApartmentSerializer(serializers.ModelSerializer):

    owner = serializers.ReadOnlyField(source="owner.email")

    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source="city",
        write_only=True
    )

    class Meta:
        model = Apartment
        fields = [
            "id",
            "title",
            "description",
            "address",
            "city",
            "city_id",
            "price_per_night",
            "rooms",
            "owner",
            "created_at",
        ]
        read_only_fields = ["owner", "created_at"]