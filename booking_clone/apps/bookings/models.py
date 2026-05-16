from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.mixins.models import TimestampedModel
from apps.properties.models import Apartment

ERR_CHECKOUT_BEFORE_CHECKIN = _('check_out must be after check_in')
ERR_DATES_OVERLAP = _('This apartment is already booked for the selected dates')


class Booking(TimestampedModel):
    """Represents a reservation for an apartment by a tenant."""

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('tenant'),
        help_text=_('The user who is making the booking.'),
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('apartment'),
        help_text=_('The apartment being booked.'),
    )
    check_in = models.DateField(
        _('check-in date'),
        db_index=True,
        help_text=_('The date the tenant plan to move in.'),
    )
    check_out = models.DateField(
        _('check-out date'),
        db_index=True,
        help_text=_('The date the tenant plan to move out.'),
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text=_('The current lifecycle stage of the booking.'),
    )
    total_price = models.DecimalField(
        _('total price'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('The total cost of the stay, auto-calculated based on nights.'),
    )

    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['tenant', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F('check_in')),
                name='booking_checkout_after_checkin',
                violation_error_message=str(ERR_CHECKOUT_BEFORE_CHECKIN),
            )
        ]

    def __str__(self) -> str:
        return f'Booking #{self.id} - {self.tenant.email} → {self.apartment.title}'

    def clean(self) -> None:
        '''Validates date order and checks for overlapping confirmed bookings.'''
        if self.check_in and self.check_out:
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
