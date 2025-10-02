from django.apps import AppConfig

class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
    
    def ready(self):
        # We'll add signals back when we have Celery installed
        # import bookings.signals
        pass