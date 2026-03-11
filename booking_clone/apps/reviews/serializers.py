from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):

    author = serializers.ReadOnlyField(source="author.email")

    class Meta:
        model = Review
        fields = [
            "id",
            "apartment",
            "author",
            "rating",
            "comment",
            "created_at",
        ]

        read_only_fields = ["author", "created_at"] 