# Python modules
from typing import Any

# Third-party modules
from rest_framework import serializers

# Project modules
from .models import Apartment, City, Country


class CountrySerializer(serializers.ModelSerializer):
    '''Serializer for Country model.'''

    class Meta:
        model = Country
        fields = ['id', 'name']


class CitySerializer(serializers.ModelSerializer):
    '''Serializer for City model; includes nested country info.'''

    country = CountrySerializer(read_only=True)
    class Meta:
        model = City
        fields = ['id', 'name', 'country']


class ApartmentReadSerializer(serializers.ModelSerializer):
    '''Serializer for reading apartment data; includes nested city and owner info.'''

    owner = serializers.ReadOnlyField(source='owner.email')
    city = CitySerializer(read_only=True)
    class Meta:
        model = Apartment
        fields = [
            'id',
            'title',
            'description',
            'address',
            'city',
            'price_per_night',
            'rooms',
            'owner',
            'created_at',
        ]
        read_only_fields = ['owner', 'created_at']


class ApartmentWriteSerializer(serializers.ModelSerializer):
    '''Serializer for creating/updating an apartment; accepts city_id instead of nested city.'''

    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        source='city',
    )

    class Meta:
        model = Apartment
        fields = [
            'title',
            'description',
            'address',
            'city_id',
            'price_per_night',
            'rooms',
        ]
        
    def create(self, validated_data: dict[str, Any]) -> Apartment:
        '''Set the owner to the authenticated user when creating an apartment.'''

        validated_data['owner'] = self.context['request'].user   
        return super().create(validated_data)
