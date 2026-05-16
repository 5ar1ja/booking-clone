from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.mixins.models import TimestampedModel
from apps.properties.models import Apartment

MIN_RATING = 1
MAX_RATING = 5


class Review(TimestampedModel):
    """Stores a renter review for an apartment they have completed a stay in."""

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("apartment"),
        help_text=_("The apartment being reviewed."),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("author"),
        help_text=_("The user who wrote the review."),
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(MIN_RATING), MaxValueValidator(MAX_RATING)],
        db_index=True,
        help_text=_("The rating given by the user (1-5)."),
    )
    comment = models.TextField(
        _("comment"),
        help_text=_("The textual feedback from the user."),
    )

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["apartment", "author"],
                name="unique_review_per_user_apartment",
            )
        ]

    def __str__(self) -> str:
        return f"Review {self.rating} stars by {self.author} for {self.apartment.title}"
