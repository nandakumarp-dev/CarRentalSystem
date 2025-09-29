from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from users.models import CarOwner
from .models import Car, Rental

class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/owner_dashboard.html'  # This template is in users folder
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get car owner profile
        car_owner = getattr(self.request.user, 'carowner', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        
        # Get actual data
        total_cars = Car.objects.filter(owner=car_owner).count()
        active_rentals = Rental.objects.filter(car__owner=car_owner, status='active').count()
        pending_requests = Rental.objects.filter(car__owner=car_owner, status='pending').count()
        
        # Get owner's cars for display
        owner_cars = Car.objects.filter(owner=car_owner)[:3]
        
        context.update({
            'owner': car_owner,
            'total_cars': total_cars,
            'active_rentals': active_rentals,
            'pending_requests': pending_requests,
            'available_cars': Car.objects.filter(owner=car_owner, is_available=True).count(),
            'owner_cars': owner_cars,
            'monthly_earnings': 0,  # Placeholder for now
            'monthly_bookings': 0,  # Placeholder for now
            'recent_activities': [],
        })
        return context

class CarListView(LoginRequiredMixin, ListView):
    model = Car
    template_name = 'rentals/car_list.html'
    context_object_name = 'cars'
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            return Car.objects.filter(owner=car_owner)
        return Car.objects.none()

class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    template_name = 'rentals/car_form.html'
    fields = ['make', 'model', 'year', 'car_type', 'daily_rate', 'description']
    success_url = reverse_lazy('rentals:my_cars')
    
    def form_valid(self, form):
        car_owner = getattr(self.request.user, 'carowner', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        form.instance.owner = car_owner
        return super().form_valid(form)

class CarUpdateView(LoginRequiredMixin, UpdateView):
    model = Car
    template_name = 'rentals/car_form.html'
    fields = ['make', 'model', 'year', 'car_type', 'daily_rate', 'is_available', 'description']
    success_url = reverse_lazy('rentals:my_cars')
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            return Car.objects.filter(owner=car_owner)
        return Car.objects.none()

class RentalListView(LoginRequiredMixin, ListView):
    model = Rental
    template_name = 'rentals/rental_list.html'
    context_object_name = 'rentals'
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            return Rental.objects.filter(car__owner=car_owner).order_by('-created_at')
        return Rental.objects.none()

class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'rentals/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owner'] = getattr(self.request.user, 'carowner', None)
        return context

class OwnerSettingsView(LoginRequiredMixin, UpdateView):
    model = CarOwner
    template_name = 'rentals/owner_settings.html'
    fields = ['company_name']
    success_url = reverse_lazy('rentals:owner_dashboard')
    
    def get_object(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        return car_owner
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the owner object to context for the template
        context['owner'] = self.get_object()
        return context