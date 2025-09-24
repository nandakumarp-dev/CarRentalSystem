from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ACCOUNT_TYPES = (
        ('customer', 'Customer'),
        ('owner', 'Rental Owner'),
    )
    
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)

class CarOwner(models.Model):  # Instead of RentalOwner
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)