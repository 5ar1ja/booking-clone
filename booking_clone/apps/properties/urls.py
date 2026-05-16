from rest_framework.routers import DefaultRouter

from django.urls import path, include

from .views import ApartmentViewSet

router = DefaultRouter()
router.register(r'apartments', ApartmentViewSet, basename='apartment')

urlpatterns = [
    path('', include(router.urls)),
]
