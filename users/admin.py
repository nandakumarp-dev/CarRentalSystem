from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Customer, CarOwner

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'account_type', 'is_staff', 'is_active')
    list_filter = ('account_type', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('account_type', 'phone_number', 'is_verified')}),
    )

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'city', 'country')
    list_filter = ('city', 'country')
    search_fields = ('user__username', 'user__email', 'driver_license_number')
    raw_id_fields = ('user',)

@admin.register(CarOwner)
class CarOwnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'verified', 'created_at')
    list_filter = ('verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'company_name', 'tax_id')
    raw_id_fields = ('user',)