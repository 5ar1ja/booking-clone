from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet

from apps.properties.models import City
from apps.properties.serializers import CitySerializer

# Create your views here.

class CityViewSet(ModelViewSet):
    queryset = City.objects.all().order_by("-created_at")
    serializer_class = CitySerializer