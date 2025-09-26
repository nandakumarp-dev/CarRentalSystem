from django.urls import path
from .views import HomeView, SignUpView, CustomLoginView, CustomLogoutView, OwnerDashboardView, CustomerDashboardView

app_name = 'users'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('owner-dashboard/', OwnerDashboardView.as_view(), name='owner_dashboard'),
    path('customer-dashboard/', CustomerDashboardView.as_view(), name='customer_dashboard'),
]