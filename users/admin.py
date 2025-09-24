from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Customer, CarOwner

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'account_type', 'first_name', 'last_name', 'is_staff')
    list_filter = ('account_type', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('account_type', 'phone_number')}),
    )

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth')

@admin.register(CarOwner)
class RentalOwnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'verified')