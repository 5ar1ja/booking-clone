# Django modules
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    """Represents a country used for apartment location filtering."""

    name = models.CharField(
        _("name"),
        max_length=100,
        unique=True,
        help_text=_("The unique name of the country."),
    )

    class Meta:
        verbose_name = _("country")
        verbose_name_plural = _("countries")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class City(models.Model):
    """Represents a city belonging to a country."""

    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("The name of the city."),
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cities",
        verbose_name=_("country"),
        help_text=_("The country this city belongs to."),
    )

    class Meta:
        unique_together = ["name", "country"]
        verbose_name = _("city")
        verbose_name_plural = _("cities")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name}, {self.country}"


class Apartment(models.Model):
    """Represents a rental apartment listing owned by a landlord."""

    title = models.CharField(
        _("title"),
        max_length=255,
        help_text=_("The title of the apartment listing."),
    )
    description = models.TextField(
        _("description"),
        help_text=_("A detailed description of the apartment."),
    )
    address = models.CharField(
        _("address"),
        max_length=255,
        help_text=_("The physical address of the apartment."),
    )
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="apartments",
        verbose_name=_("city"),
        help_text=_("The city where the apartment is located."),
    )
    price_per_night = models.DecimalField(
        _("price per night"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        db_index=True,
        help_text=_("The cost to rent the apartment for one night."),
    )
    rooms = models.PositiveIntegerField(
        _("rooms"),
        validators=[MinValueValidator(1)],
        db_index=True,
        help_text=_("The number of rooms available in the apartment."),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="apartments",
        verbose_name=_("owner"),
        help_text=_("The user who owns this apartment listing."),
    )
    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
        db_index=True,
        help_text=_("The date and time when the listing was created."),
    )

    class Meta:
        verbose_name = _("apartment")
        verbose_name_plural = _("apartments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
