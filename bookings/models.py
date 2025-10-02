from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from rentals.models import Car

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255, blank=True, null=True)
    special_requests = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['car', 'start_date', 'end_date']),
            models.Index(fields=['status', 'payment_status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            )
        ]
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"Booking #{self.id} - {self.customer.username} - {self.car}"
    
    def save(self, *args, **kwargs):
        # Calculate total days automatically
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days
            if self.total_days > 0 and hasattr(self, 'car') and self.car:
                self.total_amount = self.total_days * self.car.daily_rate
        
        # Update car availability based on booking status
        if self.pk:
            old_status = Booking.objects.get(pk=self.pk).status
            if old_status != self.status:
                self.update_car_availability()
        else:
            # New booking - make car temporarily unavailable
            if self.status in ['confirmed', 'active']:
                self.car.is_available = False
                self.car.save()
        
        super().save(*args, **kwargs)
    
    def update_car_availability(self):
        """Update car availability based on booking status"""
        if self.status in ['confirmed', 'active']:
            self.car.is_available = False
        elif self.status in ['completed', 'cancelled']:
            # Check if there are no other active bookings for this car
            active_bookings = Booking.objects.filter(
                car=self.car,
                status__in=['confirmed', 'active'],
            ).exclude(pk=self.pk)
            if not active_bookings.exists():
                self.car.is_available = True
        self.car.save()
    
    @property
    def is_active(self):
        return self.status in ['confirmed', 'active']
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']
    
    @property
    def days_until_start(self):
        today = timezone.now().date()
        return (self.start_date - today).days if self.start_date > today else 0
    
    @property
    def is_overdue(self):
        return self.status == 'active' and self.end_date < timezone.now().date()

class BookingPayment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=50, default='card')
    paid_at = models.DateTimeField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking Payment'
        verbose_name_plural = 'Booking Payments'
    
    def __str__(self):
        return f"Payment for Booking #{self.booking.id}"

class BookingReview(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking Review'
        verbose_name_plural = 'Booking Reviews'
    
    def __str__(self):
        return f"Review for Booking #{self.booking.id} - {self.rating} stars"

class FavoriteCar(models.Model):
    """Model for customers to favorite cars"""
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['customer', 'car']
        verbose_name = 'Favorite Car'
        verbose_name_plural = 'Favorite Cars'
    
    def __str__(self):
        return f"{self.customer.username} - {self.car}"