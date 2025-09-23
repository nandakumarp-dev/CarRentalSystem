from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser

class RoleChoice(models.TextChoices):

    SUPER_ADMIN = 'super_admin', 'Super Admin'

    RENTAL_OWNER = 'rental_owner', 'Rental Owner'

    CUSTOMER = 'customer', 'Customer'

class Profile(AbstractUser):

    role = models.CharField(max_length=15,choices=RoleChoice.choices,default=RoleChoice.CUSTOMER)

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.role})'
    
    class Meta:

        verbose_name = 'Profile'

        verbose_name_plural = 'Profiles'







