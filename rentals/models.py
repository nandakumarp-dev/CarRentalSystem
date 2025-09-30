from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User, CarOwner

class Car(models.Model):
    CAR_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('compact', 'Compact'),
        ('luxury', 'Luxury'),
        ('sports', 'Sports'),
        ('van', 'Van'),
        ('convertible', 'Convertible'),
    ]
    
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]
    
    TRANSMISSION_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ]
    
    owner = models.ForeignKey(CarOwner, on_delete=models.CASCADE, related_name='cars')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1990), MaxValueValidator(2025)]
    )
    car_type = models.CharField(max_length=20, choices=CAR_TYPES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='petrol')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_TYPES, default='automatic')
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    seats = models.PositiveIntegerField(default=5)
    color = models.CharField(max_length=50, blank=True)
    license_plate = models.CharField(max_length=20, unique=True, blank=True)
    mileage = models.PositiveIntegerField(blank=True, null=True)
    
    # Location
    pickup_location = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Car features
    features = models.JSONField(default=list, blank=True)
    
    # Images
    image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Car'
        verbose_name_plural = 'Cars'
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.license_plate}"
    
    @property
    def full_name(self):
        return f"{self.year} {self.make} {self.model}"
    
    @property
    def is_active(self):
        return self.is_available and not self.rentals.filter(status__in=['active', 'pending']).exists()

class Rental(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Rental details
    pickup_location = models.CharField(max_length=200, blank=True)
    dropoff_location = models.CharField(max_length=200, blank=True)
    special_requests = models.TextField(blank=True)
    
    # Payment info
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rental'
        verbose_name_plural = 'Rentals'
    
    def __str__(self):
        return f"Rental #{self.id} - {self.car} by {self.customer.username}"
    
    def save(self, *args, **kwargs):
        # Calculate total days and amount automatically
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days
            if self.total_days > 0 and self.car:
                self.total_amount = self.total_days * self.car.daily_rate
        super().save(*args, **kwargs)
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']
    
    @property
    def can_be_approved(self):
        return self.status == 'pending'
    
    @property
    def can_be_completed(self):
        return self.status == 'active'

class Review(models.Model):
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.rental.car} - {self.rating} stars"