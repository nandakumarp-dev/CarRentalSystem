from django.urls import path
from django.views.generic import RedirectView
from .views import (
    HomeView, SignUpView, CustomLoginView, CustomLogoutView, 
    ProfileUpdateView, UserUpdateView
)

app_name = 'users'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/user/', UserUpdateView.as_view(), name='user_update'),
    
    # Redirects for backward compatibility
    path('customer-dashboard/', RedirectView.as_view(pattern_name='bookings:customer_dashboard'), name='customer_dashboard'),
    path('owner-dashboard/', RedirectView.as_view(pattern_name='rentals:owner_dashboard'), name='owner_dashboard'),
]