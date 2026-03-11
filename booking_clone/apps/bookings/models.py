from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.properties.models import Apartment


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="booking"
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="booking"
    )

    check_in = models.DateField()
    check_out = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} - {self.tenant.email} → {self.apartment.title}"

    def clean(self):
        if self.check_in > self.check_out:
            raise ValidationError("chack_out must be after check_in")
        
        overlapping = Booking.objects.filter(
            apartment=self.apartment,
            status__id=[self.Status.PENDING, self.Status.CONFIRMED],
            check_in__lf=self.check_out,
            check_out__gt=self.check_in,
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("This apartment is alredy booked for the selected dates")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        # Автоматически считает total_price
        nights = (self.check_out - self.check_in).days
        self.total_price = nights * self.apartment.price_per_night
        super().save(*args, **kwargs)