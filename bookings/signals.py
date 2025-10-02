from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Booking, BookingReview
from carrentalsystem.email_backends import EmailService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Booking)
def handle_booking_status_change(sender, instance, created, **kwargs):
    """Handle booking status changes and send notifications"""
    if created:
        # New booking created
        EmailService.send_owner_notification(instance, 'Booking Request')
        logger.info(f"New booking created: #{instance.id}")
    else:
        # Booking updated - check if status changed
        try:
            old_instance = Booking.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == 'confirmed':
                    EmailService.send_booking_confirmation(instance)
                elif instance.status == 'cancelled':
                    EmailService.send_booking_cancellation(instance)
                logger.info(f"Booking #{instance.id} status changed from {old_instance.status} to {instance.status}")
        except Booking.DoesNotExist:
            pass

@receiver(post_save, sender=BookingReview)
def handle_new_review(sender, instance, created, **kwargs):
    """Handle new review creation"""
    if created:
        logger.info(f"New review created for booking #{instance.booking.id} with rating {instance.rating}")

@receiver(post_delete, sender=Booking)
def handle_booking_deletion(sender, instance, **kwargs):
    """Handle booking deletion"""
    logger.warning(f"Booking #{instance.id} was deleted")