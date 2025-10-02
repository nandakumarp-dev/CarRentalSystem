from django.contrib import admin
from .models import Car, Rental, Review, CarImage

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'car_type', 'daily_rate', 'is_available', 'owner', 'city')
    list_filter = ('car_type', 'fuel_type', 'transmission', 'is_available', 'is_active', 'created_at')
    search_fields = ('make', 'model', 'license_plate', 'city')
    list_editable = ('is_available', 'daily_rate')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('owner',)

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'customer', 'start_date', 'end_date', 'status', 'payment_status', 'total_amount')
    list_filter = ('status', 'payment_status', 'start_date', 'end_date', 'created_at')
    search_fields = ('car__make', 'car__model', 'customer__username', 'customer__email')
    readonly_fields = ('created_at', 'updated_at', 'total_amount', 'total_days')
    raw_id_fields = ('car', 'customer')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('rental', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('rental__car__make', 'rental__car__model', 'rental__customer__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('rental',)

@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display = ('car', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('car__make', 'car__model')
    raw_id_fields = ('car',)