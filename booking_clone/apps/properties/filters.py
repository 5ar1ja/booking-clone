import django_filters

from .models import Apartment


class ApartmentFilter(django_filters.FilterSet):
    '''Filter apartments by city, number of rooms, and price range.'''

    min_price = django_filters.NumberFilter(
        field_name='price_per_night',
        lookup_expr='gte',
    )
    max_price = django_filters.NumberFilter(
        field_name='price_per_night',
        lookup_expr='lte',
    )
    # allows "?country=1" instead of "?city__country=1"
    country = django_filters.NumberFilter(field_name='city__country', lookup_expr='exact')

    class Meta:
        model = Apartment
        fields = ['city', 'rooms']
