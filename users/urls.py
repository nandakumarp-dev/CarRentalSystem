from django.urls import path
from django.views.generic import RedirectView
from .views import HomeView, SignUpView, CustomLoginView, CustomLogoutView, CustomerDashboardView

app_name = 'users'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('customer-dashboard/', CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('owner-dashboard/', RedirectView.as_view(url='/rentals/owner/dashboard/'), name='owner_dashboard'),
]