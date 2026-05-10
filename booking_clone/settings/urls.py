from django.contrib import admin
from django.urls import path, include
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),

    #apps urls
    path('users/', include('apps.users.urls')),
    path('properties/', include('apps.properties.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('bookings/', include('apps.bookings.urls'))
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns