from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    path('owner/dashboard/', views.OwnerDashboardView.as_view(), name='owner_dashboard'),
    path('owner/cars/add/', views.CarCreateView.as_view(), name='add_car'),
    path('owner/cars/', views.CarListView.as_view(), name='my_cars'),
    path('owner/cars/<int:pk>/edit/', views.CarUpdateView.as_view(), name='edit_car'),
    path('owner/rentals/', views.RentalListView.as_view(), name='rentals'),
    path('owner/analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('owner/settings/', views.OwnerSettingsView.as_view(), name='owner_settings'),
]