# Django modules
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

# Third-party modules
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # apps urls
    path('users/', include('apps.users.urls')),
    path('properties/', include('apps.properties.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('notifications/', include('apps.notifications.urls')),

    # Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns