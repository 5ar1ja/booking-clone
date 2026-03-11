from django.db import models
from django.conf import settings
from apps.properties.models import Apartment
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    author = models.ForeignKey( # renter
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["apartment", "author"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review {self.rating} stars by {self.author} for {self.apartment.title}"