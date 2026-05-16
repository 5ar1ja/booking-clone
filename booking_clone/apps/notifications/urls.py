# Django modules
from django.urls import include, path

# Third-party modules
from rest_framework.routers import DefaultRouter

# Project modules
from .views import NotificationViewSet, stream_notifications


router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('stream/', stream_notifications, name='notification-stream'),
    path('', include(router.urls)),
]
