import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class EmailService:
    """Service class for sending emails"""
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation email"""
        try:
            subject = f"Booking Confirmation - #{booking.id}"
            html_message = render_to_string('emails/booking_confirmation.html', {
                'booking': booking,
                'customer': booking.customer,
                'car': booking.car,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.customer.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Booking confirmation email sent for booking #{booking.id}")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email: {str(e)}")
    
    @staticmethod
    def send_booking_cancellation(booking):
        """Send booking cancellation email"""
        try:
            subject = f"Booking Cancelled - #{booking.id}"
            html_message = render_to_string('emails/booking_cancellation.html', {
                'booking': booking,
                'customer': booking.customer,
                'car': booking.car,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.customer.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Booking cancellation email sent for booking #{booking.id}")
        except Exception as e:
            logger.error(f"Failed to send booking cancellation email: {str(e)}")
    
    @staticmethod
    def send_owner_notification(booking, notification_type):
        """Send notification to car owner"""
        try:
            owner = booking.car.owner.user
            subject = f"New {notification_type} - Booking #{booking.id}"
            html_message = render_to_string('emails/owner_notification.html', {
                'booking': booking,
                'notification_type': notification_type,
                'owner': owner,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[owner.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Owner notification email sent for booking #{booking.id}")
        except Exception as e:
            logger.error(f"Failed to send owner notification email: {str(e)}")