# Python modules
from typing import Any

# Django modules
from django.db.models import QuerySet

# Third-party modules
import django_filters

# Project modules
from apps.bookings.models import Booking
from .models import Apartment


class ApartmentFilter(django_filters.FilterSet):

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

    check_in = django_filters.DateFilter(method='filter_availability')
    check_out = django_filters.DateFilter(method='filter_availability')

    class Meta:
        model = Apartment
        fields = ['city', 'rooms']

    def filter_availability(self, queryset: QuerySet[Apartment], name: str, value: Any) -> QuerySet[Apartment]:
        """
        Excludes apartments that have overlapping bookings for the given dates.
        Requires both check_in and check_out to be present in the request.
        """
        check_in = self.data.get('check_in')
        check_out = self.data.get('check_out')

        if check_in and check_out:
            # Logic: Overlap if (booking.check_in < search.check_out) AND (booking.check_out > search.check_in)
            # Only consider PENDING and CONFIRMED bookings.
            overlapping_bookings = Booking.objects.filter(
                status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
                check_in__lt=check_out,
                check_out__gt=check_in
            )
            
            # Exclude apartments associated with overlapping bookings
            queryset = queryset.exclude(
                id__in=overlapping_bookings.values_list('apartment_id', flat=True)
            )

        return queryset
