import django_filters
from .models import Review


class ReviewFilter(django_filters.FilterSet):
    '''Filter reviews by apartment, author, and rating range.'''

    min_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte'
    )

    max_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='lte'
    )

    class Meta:
        model = Review
        fields = [
            'apartment',
            'author',
            'rating',
        ]
