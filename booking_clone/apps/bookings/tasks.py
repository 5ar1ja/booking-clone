import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import DatabaseError
from django.utils import timezone

from apps.bookings.models import Booking

logger = logging.getLogger('apps.bookings')

# Configuration Constants
STALE_BOOKING_THRESHOLD_HOURS = 24


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_booking_confirmation_email(booking_id: int):
    '''
    Sends a confirmation email to the tenant when a booking is confirmed.
    
    Automatic retries are enabled to handle temporary SMTP or Database issues.
    '''
    try:
        booking = Booking.objects.select_related('apartment', 'tenant').get(id=booking_id)
    except Booking.DoesNotExist:
        logger.error(f'Task aborted: Booking {booking_id} no longer exists.')
        return

    subject = f'Booking Confirmed: {booking.apartment.title}'
    message = (
        f'Hello {booking.tenant.first_name},\n\n'
        f'Your booking for "{booking.apartment.title}" has been confirmed!\n'
        f'Check-in: {booking.check_in}\n'
        f'Check-out: {booking.check_out}\n\n'
        f'Enjoy your stay!'
    )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.tenant.email],
        fail_silently=False,
    )
    logger.info(f'Confirmation email sent for booking {booking_id} to {booking.tenant.email}')


@shared_task(
    autoretry_for=(DatabaseError,),
    retry_backoff=True,
    max_retries=2,
)
def cleanup_stale_bookings():
    '''
    Periodical task to cancel PENDING bookings older than threshold.
    
    Uses retries to handle potential database locks during mass updates.
    '''
    threshold = timezone.now() - timedelta(hours=STALE_BOOKING_THRESHOLD_HOURS)
    
    stale_bookings = Booking.objects.filter(
        status=Booking.Status.PENDING,
        created_at__lt=threshold
    )
    
    count = stale_bookings.count()
    if count > 0:
        stale_bookings.update(status=Booking.Status.CANCELLED)
        logger.info(f'Cleanup: Cancelled {count} stale pending bookings (Threshold: {STALE_BOOKING_THRESHOLD_HOURS}h).')
    else:
        logger.info('Cleanup: No stale bookings found.')
    
    return count
