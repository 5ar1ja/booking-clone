# Third-party modules
from rest_framework.routers import DefaultRouter

# Project modules
from .views import ReviewViewSet


router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='review')

urlpatterns = router.urls
