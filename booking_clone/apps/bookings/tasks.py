import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger('apps.bookings')

@shared_task
def send_booking_confirmation_email(booking_id: int):
    '''
    Sends a confirmation email to the tenant when a booking is confirmed.
    Executed as a delayed celery task.
    '''
    from apps.bookings.models import Booking
    
    try:
        booking = Booking.objects.select_related('apartment', 'tenant').get(id=booking_id)
        
        subject = f'Booking Confirmed: {booking.apartment.title}'
        message = (
            f'Hello {booking.tenant.first_name},\n\n'
            f'Your booking for "{booking.apartment.title}" has been confirmed!\n'
            f'Check-in: {booking.check_in}\n'
            f'Check-out: {booking.check_out}\n\n'
            f'Enjoy your stay!'
        )
        recipient_list = [booking.tenant.email]
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f'Confirmation email sent for booking {booking_id} to {booking.tenant.email}')
        
    except Booking.DoesNotExist:
        logger.error(f'Could not send confirmation email: Booking {booking_id} does not exist.')
    except Exception as e:
        logger.exception(f'Error sending confirmation email for booking {booking_id}: {str(e)}')
