from rest_framework import serializers

from apps.properties.models import City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "country", "created_at"]
        read_only_fields = ["id", "created_at"]
