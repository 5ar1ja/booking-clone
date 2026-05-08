from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.properties.models import Apartment

ERR_CHECKOUT_BEFORE_CHECKIN = 'check_out must be after check_in'
ERR_DATES_OVERLAP = 'This apartment is already booked for the selected dates'


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Booking #{self.id} - {self.tenant.email} → {self.apartment.title}'

    def clean(self) -> None:
        '''Validates date order and checks for overlapping confirmed bookings.'''
        if self.check_in >= self.check_out:
            raise ValidationError(ERR_CHECKOUT_BEFORE_CHECKIN)

        overlapping = Booking.objects.filter(
            apartment=self.apartment,
            status__in=[self.Status.PENDING, self.Status.CONFIRMED],
            check_in__lt=self.check_out,
            check_out__gt=self.check_in,
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(ERR_DATES_OVERLAP)

    def save(self, *args: Any, **kwargs: Any) -> None:
        '''Runs full validation and auto-calculates total_price before saving.'''
        self.full_clean()
        nights = (self.check_out - self.check_in).days
        self.total_price = nights * self.apartment.price_per_night
        super().save(*args, **kwargs)
