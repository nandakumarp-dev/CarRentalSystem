from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

class Car(models.Model):
    CAR_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('compact', 'Compact'),
        ('luxury', 'Luxury'),
        ('sports', 'Sports'),
        ('van', 'Van'),
        ('convertible', 'Convertible'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]
    
    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
    ]
    
    TRANSMISSION_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ]
    
    owner = models.ForeignKey('users.CarOwner', on_delete=models.CASCADE, related_name='cars')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1990), MaxValueValidator(timezone.now().year + 1)]
    )
    car_type = models.CharField(max_length=20, choices=CAR_TYPES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='petrol')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_TYPES, default='automatic')
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    seats = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(20)])
    color = models.CharField(max_length=50, blank=True)
    license_plate = models.CharField(max_length=20, unique=True)
    mileage = models.PositiveIntegerField(blank=True, null=True)
    
    # Location
    pickup_location = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Car features
    features = models.JSONField(default=list, blank=True)
    
    # Images
    image = models.ImageField(upload_to='car_images/')
    image_2 = models.ImageField(upload_to='car_images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='car_images/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Car'
        verbose_name_plural = 'Cars'
        indexes = [
            models.Index(fields=['is_available', 'is_active']),
            models.Index(fields=['car_type', 'fuel_type']),
            models.Index(fields=['daily_rate']),
            models.Index(fields=['city']),
        ]
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.license_plate}"
    
    @property
    def full_name(self):
        return f"{self.year} {self.make} {self.model}"
    
    @property
    def is_rentable(self):
        """Check if car can be rented (available and no active rentals)"""
        if not self.is_available or not self.is_active:
            return False
        
        # Check for active rentals
        active_rentals = self.rentals.filter(
            status__in=['pending', 'confirmed', 'active'],
            end_date__gte=timezone.now().date()
        )
        return not active_rentals.exists()
    
    @property
    def average_rating(self):
        """Calculate average rating from completed rentals with reviews"""
        reviews = Review.objects.filter(rental__car=self, rental__status='completed')
        if reviews.exists():
            return round(reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'], 1)
        return 0
    
    @property
    def total_reviews(self):
        return Review.objects.filter(rental__car=self, rental__status='completed').count()

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
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Rental details
    pickup_location = models.CharField(max_length=200)
    dropoff_location = models.CharField(max_length=200, blank=True)
    special_requests = models.TextField(blank=True)
    
    # Payment info
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_intent_id = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rental'
        verbose_name_plural = 'Rentals'
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
    
    def __str__(self):
        return f"Rental #{self.id} - {self.car} by {self.customer.username}"
    
    def save(self, *args, **kwargs):
        # Calculate total days and amount automatically
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days
            if self.total_days > 0 and self.car:
                self.total_amount = self.total_days * self.car.daily_rate
        
        # Update car availability
        if self.pk:
            old_status = Rental.objects.get(pk=self.pk).status
            if old_status != self.status:
                self.update_car_availability(old_status)
        else:
            if self.status in ['confirmed', 'active']:
                self.car.is_available = False
                self.car.save()
        
        super().save(*args, **kwargs)
    
    def update_car_availability(self, old_status):
        """Update car availability when rental status changes"""
        if self.status in ['confirmed', 'active']:
            self.car.is_available = False
        elif self.status in ['completed', 'cancelled', 'rejected']:
            # Check if there are no other active rentals for this car
            active_rentals = Rental.objects.filter(
                car=self.car,
                status__in=['pending', 'confirmed', 'active'],
            ).exclude(pk=self.pk)
            if not active_rentals.exists():
                self.car.is_available = True
        self.car.save()
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']
    
    @property
    def can_be_approved(self):
        return self.status == 'pending'
    
    @property
    def can_be_completed(self):
        return self.status == 'active'
    
    @property
    def days_until_start(self):
        today = timezone.now().date()
        return (self.start_date - today).days if self.start_date > today else 0
    
    @property
    def is_overdue(self):
        return self.status == 'active' and self.end_date < timezone.now().date()

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        indexes = [
            models.Index(fields=['rental']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"Review for {self.rental.car} - {self.rating} stars"

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    caption = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']
        verbose_name = 'Car Image'
        verbose_name_plural = 'Car Images'
    
    def __str__(self):
        return f"Image for {self.car}"