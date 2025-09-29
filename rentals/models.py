from django.db import models
from users.models import User, CarOwner

class Car(models.Model):
    CAR_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('compact', 'Compact'),
        ('luxury', 'Luxury'),
    ]
    
    owner = models.ForeignKey(CarOwner, on_delete=models.CASCADE, related_name='cars')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    car_type = models.CharField(max_length=20, choices=CAR_TYPES)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model}"

class Rental(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField()
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rental #{self.id} - {self.car}"