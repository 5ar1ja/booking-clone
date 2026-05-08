from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.properties.models import Apartment

MIN_RATING = 1
MAX_RATING = 5


class Review(models.Model):
    '''Stores a renter review for an apartment they have completed a stay in.'''

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)],
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['apartment', 'author']
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Review {self.rating} stars by {self.author} for {self.apartment.title}'
