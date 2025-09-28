from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404
from users.models import CarOwner  # Changed import
from .models import Car, Rental

class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'rentals/owner_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get car owner profile or create one if it doesn't exist
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        
        # Get actual data
        total_cars = Car.objects.filter(owner=car_owner).count()
        active_rentals = Rental.objects.filter(car__owner=car_owner, status='active').count()
        pending_requests = Rental.objects.filter(car__owner=car_owner, status='pending').count()
        available_cars = Car.objects.filter(owner=car_owner, is_available=True).count()
        
        # Get owner's cars for display
        owner_cars = Car.objects.filter(owner=car_owner)[:3]
        
        # Calculate monthly earnings
        monthly_earnings = self.calculate_monthly_earnings(car_owner)
        
        context.update({
            'owner': car_owner,  # Now using car_owner
            'total_cars': total_cars,
            'active_rentals': active_rentals,
            'pending_requests': pending_requests,
            'available_cars': available_cars,
            'owner_cars': owner_cars,
            'monthly_earnings': monthly_earnings,
            'monthly_bookings': Rental.objects.filter(
                car__owner=car_owner, 
                created_at__month=timezone.now().month
            ).count(),
            'recent_activities': self.get_recent_activities(car_owner),
        })
        return context
    
    def calculate_monthly_earnings(self, car_owner):
        from django.db.models import Sum
        monthly_rentals = Rental.objects.filter(
            car__owner=car_owner,
            created_at__month=timezone.now().month,
            status__in=['completed', 'active'],
            payment_status=True
        )
        total = monthly_rentals.aggregate(Sum('total_amount'))['total_amount__sum']
        return total if total else 0
    
    def get_recent_activities(self, car_owner):
        recent_rentals = Rental.objects.filter(car__owner=car_owner).order_by('-created_at')[:3]
        activities = []
        
        for rental in recent_rentals:
            if rental.status == 'pending':
                activities.append({
                    'title': 'New booking request',
                    'description': f'{rental.car.make} {rental.car.model} - {rental.total_days} days',
                    'time': self.get_time_ago(rental.created_at),
                    'status_color': 'success',
                    'status_text': 'Pending approval'
                })
            elif rental.status == 'active':
                activities.append({
                    'title': 'Rental started',
                    'description': f'{rental.car.make} {rental.car.model} - Active rental',
                    'time': self.get_time_ago(rental.created_at),
                    'status_color': 'primary',
                    'status_text': 'In progress'
                })
            elif rental.status == 'completed':
                activities.append({
                    'title': 'Rental completed',
                    'description': f'{rental.car.make} {rental.car.model} - ${rental.total_amount}',
                    'time': self.get_time_ago(rental.created_at),
                    'status_color': 'info',
                    'status_text': 'Completed'
                })
        
        return activities
    
    def get_time_ago(self, timestamp):
        from django.utils import timezone
        now = timezone.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minutes ago"
        else:
            return "Just now"

class CarListView(LoginRequiredMixin, ListView):
    model = Car
    template_name = 'rentals/car_list.html'
    context_object_name = 'cars'
    
    def get_queryset(self):
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        return Car.objects.filter(owner=car_owner)

class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    template_name = 'rentals/car_form.html'
    fields = ['make', 'model', 'year', 'car_type', 'fuel_type', 'transmission', 
              'daily_rate', 'seats', 'color', 'license_plate', 'description']
    success_url = reverse_lazy('rentals:my_cars')
    
    def form_valid(self, form):
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        form.instance.owner = car_owner
        return super().form_valid(form)

class CarUpdateView(LoginRequiredMixin, UpdateView):
    model = Car
    template_name = 'rentals/car_form.html'
    fields = ['make', 'model', 'year', 'car_type', 'fuel_type', 'transmission', 
              'daily_rate', 'is_available', 'seats', 'color', 'license_plate', 'description']
    success_url = reverse_lazy('rentals:my_cars')
    
    def get_queryset(self):
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        return Car.objects.filter(owner=car_owner)

class RentalListView(LoginRequiredMixin, ListView):
    model = Rental
    template_name = 'rentals/rental_list.html'
    context_object_name = 'rentals'
    
    def get_queryset(self):
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        return Rental.objects.filter(car__owner=car_owner).order_by('-created_at')

class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'rentals/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        
        # Add analytics data here
        context['owner'] = car_owner
        return context

class OwnerSettingsView(LoginRequiredMixin, UpdateView):
    model = CarOwner  # Changed to CarOwner
    template_name = 'rentals/owner_settings.html'
    fields = ['company_name']  # Add other fields from CarOwner model as needed
    success_url = reverse_lazy('rentals:owner_dashboard')
    
    def get_object(self):
        car_owner, created = CarOwner.objects.get_or_create(user=self.request.user)
        return car_owner