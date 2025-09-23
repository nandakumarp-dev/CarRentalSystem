from django.db import models
from users.models import Profile

# Create your models here.

class Brand(models.Model):

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):

        return self.name

class VehicleType(models.Model):

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):

        return self.name
    
class Feature(models.Model):

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):

        return self.name

class Vehicle(models.Model):

    TRANSMISSION_CHOICES = [('manual', 'Manual'),('automatic', 'Automatic'),]
    
    AVAILABILITY_CHOICES = [('available', 'Available'),('booked', 'Booked'),('maintenance', 'Maintenance'),]
    
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'rental_owner'})

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    transmission_type = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES)
    
    license_plate = models.CharField(max_length=20, unique=True)

    availability_status = models.CharField(max_length=15, choices=AVAILABILITY_CHOICES, default='available')

    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)

    daily_rent = models.DecimalField(max_digits=10, decimal_places=2)

    late_return_fee = models.DecimalField(max_digits=10, decimal_places=2)

    features = models.ManyToManyField(Feature, blank=True)
    
    def __str__(self):

        return f"{self.brand} {self.name}"

class VehicleImage(models.Model):

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')

    image = models.ImageField(upload_to='vehicle_images/')
    
    def __str__(self):

        return f"Image for {self.vehicle}"
