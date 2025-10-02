from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update booking statuses (e.g., mark active bookings as completed when end date passes)'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Mark active bookings as completed if end date has passed
        completed_count = Booking.objects.filter(
            status='active',
            end_date__lt=today
        ).update(status='completed')
        
        # Mark confirmed bookings as active if start date has arrived
        active_count = Booking.objects.filter(
            status='confirmed',
            start_date__lte=today
        ).update(status='active')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {completed_count} completed and {active_count} active bookings.'
            )
        )
        logger.info(f"Booking status update: {completed_count} completed, {active_count} activated")