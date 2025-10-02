from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    
    # Bookings
    path('my-bookings/', views.BookingListView.as_view(), name='my_bookings'),
    path('booking/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('book/<int:car_id>/', views.BookingCreateView.as_view(), name='create_booking'),
    path('booking/<int:pk>/cancel/', views.BookingCancelView.as_view(), name='cancel_booking'),
    path('rental-history/', views.RentalHistoryView.as_view(), name='rental_history'),
    
    # Reviews
    path('booking/<int:booking_id>/review/', views.ReviewCreateView.as_view(), name='create_review'),
    
    # Payments
    path('booking/<int:pk>/payment/', views.BookingPaymentView.as_view(), name='booking_payment'),
    path('booking/<int:pk>/process-payment/', views.ProcessPaymentView.as_view(), name='process_payment'),
    path('webhooks/payment/', views.PaymentWebhookView.as_view(), name='payment_webhook'),
    
    # Favorites
    path('favorites/', views.FavoriteListView.as_view(), name='favorite_cars'),
    path('favorite/<int:car_id>/', views.FavoriteCarView.as_view(), name='toggle_favorite'),
    
    # API Endpoints
    path('api/car/<int:car_id>/availability/', views.BookingAvailabilityCheckView.as_view(), name='check_availability'),
]