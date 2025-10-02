from django.core.management.base import BaseCommand
from rentals.models import Car, Rental
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update car availability based on current rentals'
    
    def handle(self, *args, **options):
        updated_count = 0
        
        for car in Car.objects.all():
            # Check if car has any active rentals
            has_active_rentals = Rental.objects.filter(
                car=car,
                status__in=['pending', 'confirmed', 'active'],
                end_date__gte=timezone.now().date()
            ).exists()
            
            # Update availability
            new_availability = not has_active_rentals
            if car.is_available != new_availability:
                car.is_available = new_availability
                car.save()
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated availability for {updated_count} cars.')
        )
        logger.info(f"Car availability update: {updated_count} cars updated")