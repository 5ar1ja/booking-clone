# Django modules
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

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
    path('i18n/', include('django.conf.urls.i18n')),
    path(
        'localization/',
        TemplateView.as_view(template_name='localization/demo.html'),
        name='localization-demo',
    ),

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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
