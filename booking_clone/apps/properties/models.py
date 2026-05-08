from django.conf import settings
from django.db import models


class Country(models.Model):
    '''Represents a country used for apartment location filtering.'''

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Countries'

    def __str__(self) -> str:
        return self.name


class City(models.Model):
    '''Represents a city belonging to a country.'''

    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cities',
    )

    class Meta:
        unique_together = ['name', 'country']
        verbose_name_plural = 'Cities'

    def __str__(self) -> str:
        return f'{self.name}, {self.country}'


class Apartment(models.Model):
    '''Represents a rental apartment listing owned by a landlord.'''

    title = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='apartments')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    rooms = models.IntegerField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apartments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
