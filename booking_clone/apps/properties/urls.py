# Django modules
from django.urls import path, include

# Third-party modules
from rest_framework.routers import DefaultRouter

# Project modules
from .views import ApartmentViewSet


router = DefaultRouter()
router.register(r'apartments', ApartmentViewSet, basename='apartment')

urlpatterns = [
    path('', include(router.urls)),
]
