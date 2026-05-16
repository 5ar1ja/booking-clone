from rest_framework import serializers

from .models import Review


class ReviewReadSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Review
        fields = [
            'apartment',
            'rating',
            'comment',
        ]

    def validate_rating(self, value: int) -> int:
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
