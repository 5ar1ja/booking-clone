# Django modules
from django.utils.translation import gettext_lazy as _

# Third-party modules
from rest_framework import serializers

# Project modules
from .models import Review

ERR_RATING_RANGE = _('Rating must be between 1 and 5.')


class ReviewReadSerializer(serializers.ModelSerializer):
    '''Serializer for reading review data; includes nested apartment and author info.'''

    author = serializers.ReadOnlyField(source='author.email')
    apartment_title = serializers.ReadOnlyField(source='apartment.title')

    class Meta:
        model = Review
        fields = [
            'id',
            'apartment',
            'apartment_title',
            'author',
            'rating',
            'comment',
            'created_at'
        ]


class ReviewWriteSerializer(serializers.ModelSerializer):
    '''Serializer for creating/updating a review; validates that rating is between 1 and 5.'''

    class Meta:
        model = Review
        fields = [
            'apartment',
            'rating',
            'comment',
        ]

    def validate_rating(self, value: int) -> int:
        '''Ensure rating is between 1 and 5.'''

        if not (1 <= value <= 5):
            raise serializers.ValidationError(ERR_RATING_RANGE)
        return value
