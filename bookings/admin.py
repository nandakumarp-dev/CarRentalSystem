from django.contrib import admin
from .models import Booking, BookingPayment, BookingReview, FavoriteCar

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'car', 'start_date', 'end_date', 'status', 'payment_status', 'total_amount')
    list_filter = ('status', 'payment_status', 'start_date', 'end_date', 'created_at')
    search_fields = ('customer__username', 'customer__email', 'car__make', 'car__model')
    readonly_fields = ('created_at', 'updated_at', 'total_amount', 'total_days')
    raw_id_fields = ('customer', 'car')
    list_editable = ('status', 'payment_status')

@admin.register(BookingPayment)
class BookingPaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'paid_at', 'created_at')
    list_filter = ('payment_method', 'paid_at', 'created_at')
    search_fields = ('booking__id', 'payment_intent_id')
    readonly_fields = ('created_at',)
    raw_id_fields = ('booking',)

@admin.register(BookingReview)
class BookingReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('booking__car__make', 'booking__car__model', 'booking__customer__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('booking',)

@admin.register(FavoriteCar)
class FavoriteCarAdmin(admin.ModelAdmin):
    list_display = ('customer', 'car', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('customer__username', 'car__make', 'car__model')
    readonly_fields = ('created_at',)
    raw_id_fields = ('customer', 'car')