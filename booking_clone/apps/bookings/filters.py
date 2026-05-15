import django_filters

from .models import Booking


class BookingFilter(django_filters.FilterSet):
    check_in_after = django_filters.DateFilter(
        field_name='check_in',
        lookup_expr='gte',
    )
    check_in_before = django_filters.DateFilter(
        field_name='check_in',
        lookup_expr='lte',
    )
    check_out_after = django_filters.DateFilter(
        field_name='check_out',
        lookup_expr='gte',
    )
    check_out_before = django_filters.DateFilter(
        field_name='check_out',
        lookup_expr='lte',
    )

    class Meta:
        model = Booking
        fields = [
            'apartment',
            'status',
            'tenant',
        ]
