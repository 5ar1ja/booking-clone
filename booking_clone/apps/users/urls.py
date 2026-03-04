from django.urls import path, include
from django.conf.urls.static import static

from rest_framework.routers import DefaultRouter

from apps.users.views import CustomUserViewSet
from settings.base import MEDIA_ROOT, MEDIA_URL

router = DefaultRouter()
router.register(r"", CustomUserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
] + static(MEDIA_URL, document_root=MEDIA_ROOT)