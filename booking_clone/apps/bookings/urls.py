# Django modules
from django.urls import path, include

# Third-party modules
from rest_framework.routers import DefaultRouter

# Project modules
from .views import BookingViewSet


router = DefaultRouter()
router.register(r'', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls))
]
