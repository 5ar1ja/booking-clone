import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def send_booking_confirmation_notification(booking_id):
    from apps.bookings.models import Booking
    try:
        booking = Booking.objects.get(id=booking_id)
        # Here we would normally send an email or push notification
        logger.info(f"Notification: Booking {booking.id} for apartment '{booking.apartment.title}' has been CONFIRMED!")
        logger.info(f"Notification Sent to Tenant: {booking.tenant.email}")
        logger.info(f"Notification Sent to Landlord: {booking.apartment.owner.email}")
        return True
    except Booking.DoesNotExist:
        logger.error(f"Booking with id {booking_id} not found.")
        return False
