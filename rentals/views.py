# source rentals/views.py

from django.views.generic import TemplateView, ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from users.models import CarOwner
from .models import Car, Rental, Review

class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/owner_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        car_owner = getattr(self.request.user, 'carowner', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        
        # Calculate time ranges
        today = timezone.now().date()
        month_start = today.replace(day=1)
        next_month = month_start + timedelta(days=32)
        next_month = next_month.replace(day=1)
        
        # Get analytics data
        monthly_earnings = Rental.objects.filter(
            car__owner=car_owner,
            created_at__date__gte=month_start,
            created_at__date__lt=next_month,
            payment_status=True
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_bookings = Rental.objects.filter(
            car__owner=car_owner,
            created_at__date__gte=month_start,
            created_at__date__lt=next_month
        ).count()
        
        # Get recent activities
        recent_rentals = Rental.objects.filter(car__owner=car_owner).order_by('-created_at')[:5]
        recent_activities = []
        
        for rental in recent_rentals:
            if rental.status == 'pending':
                recent_activities.append({
                    'title': 'New Booking Request',
                    'description': f'{rental.car.make} {rental.car.model} for {rental.total_days} days',
                    'time': self.get_time_ago(rental.created_at),
                    'status_color': 'warning',
                    'status_text': 'Pending Approval',
                    'type': 'booking'
                })
            elif rental.status == 'confirmed':
                recent_activities.append({
                    'title': 'Booking Confirmed',
                    'description': f'{rental.car.make} {rental.car.model} confirmed',
                    'time': self.get_time_ago(rental.updated_at),
                    'status_color': 'info',
                    'status_text': 'Confirmed',
                    'type': 'confirmation'
                })
            elif rental.status == 'active':
                recent_activities.append({
                    'title': 'Rental Started',
                    'description': f'{rental.car.make} {rental.car.model} is now active',
                    'time': self.get_time_ago(rental.updated_at),
                    'status_color': 'success',
                    'status_text': 'Active',
                    'type': 'rental'
                })
        
        context.update({
            'owner': car_owner,
            'total_cars': Car.objects.filter(owner=car_owner).count(),
            'active_rentals': Rental.objects.filter(car__owner=car_owner, status='active').count(),
            'pending_requests': Rental.objects.filter(car__owner=car_owner, status='pending').count(),
            'available_cars': Car.objects.filter(owner=car_owner, is_available=True).count(),
            'owner_cars': Car.objects.filter(owner=car_owner)[:6],
            'monthly_earnings': monthly_earnings,
            'monthly_bookings': monthly_bookings,
            'total_earnings': Rental.objects.filter(
                car__owner=car_owner, 
                payment_status=True
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
            'recent_activities': recent_activities,
        })
        return context
    
    def get_time_ago(self, timestamp):
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
    paginate_by = 8
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            return Car.objects.filter(owner=car_owner).select_related('owner')
        return Car.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            context['stats'] = {
                'total': Car.objects.filter(owner=car_owner).count(),
                'available': Car.objects.filter(owner=car_owner, is_available=True).count(),
                'rented': Car.objects.filter(owner=car_owner, is_available=False).count(),
            }
        return context

class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    template_name = 'rentals/car_form.html'
    fields = [
        'make', 'model', 'year', 'car_type', 'fuel_type', 'transmission',
        'daily_rate', 'seats', 'color', 'license_plate', 'mileage',
        'pickup_location', 'city', 'description', 'image', 'features'
    ]
    success_url = reverse_lazy('rentals:my_cars')
    
    def form_valid(self, form):
        car_owner = getattr(self.request.user, 'carowner', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        form.instance.owner = car_owner
        
        # Set features from form data
        features = []
        for feature in ['ac', 'bluetooth', 'gps', 'usb', 'sunroof']:
            if self.request.POST.get(feature):
                features.append(feature)
        form.instance.features = features
        
        messages.success(self.request, f"Car {form.instance.make} {form.instance.model} added successfully!")
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add CSS classes to form fields
        for field in form.fields:
            form.fields[field].widget.attrs.update({'class': 'form-control'})
        return form

class CarUpdateView(LoginRequiredMixin, UpdateView):
    model = Car
    template_name = 'rentals/car_form.html'
    fields = [
        'make', 'model', 'year', 'car_type', 'fuel_type', 'transmission',
        'daily_rate', 'is_available', 'seats', 'color', 'license_plate', 
        'mileage', 'pickup_location', 'city', 'description', 'image', 'features'
    ]
    success_url = reverse_lazy('rentals:my_cars')
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            return Car.objects.filter(owner=car_owner)
        return Car.objects.none()
    
    def form_valid(self, form):
        messages.success(self.request, f"Car {form.instance.make} {form.instance.model} updated successfully!")
        return super().form_valid(form)

class CarDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        car = get_object_or_404(Car, pk=pk, owner=request.user.carowner)
        car_name = f"{car.make} {car.model}"
        car.delete()
        messages.success(request, f"Car {car_name} deleted successfully!")
        return redirect('rentals:my_cars')

class RentalListView(LoginRequiredMixin, ListView):
    model = Rental
    template_name = 'rentals/rental_list.html'
    context_object_name = 'rentals'
    paginate_by = 10
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            status_filter = self.request.GET.get('status', 'all')
            queryset = Rental.objects.filter(car__owner=car_owner).select_related('car', 'customer')
            
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            
            return queryset.order_by('-created_at')
        return Rental.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner = getattr(self.request.user, 'carowner', None)
        if car_owner:
            context['status_filter'] = self.request.GET.get('status', 'all')
            context['status_counts'] = {
                'all': Rental.objects.filter(car__owner=car_owner).count(),
                'pending': Rental.objects.filter(car__owner=car_owner, status='pending').count(),
                'confirmed': Rental.objects.filter(car__owner=car_owner, status='confirmed').count(),
                'active': Rental.objects.filter(car__owner=car_owner, status='active').count(),
                'completed': Rental.objects.filter(car__owner=car_owner, status='completed').count(),
            }
        return context

class RentalActionView(LoginRequiredMixin, View):
    def post(self, request, pk, action):
        rental = get_object_or_404(Rental, pk=pk, car__owner=request.user.carowner)
        
        if action == 'approve' and rental.status == 'pending':
            rental.status = 'confirmed'
            rental.save()
            messages.success(request, f"Rental #{rental.id} approved successfully!")
        
        elif action == 'reject' and rental.status == 'pending':
            rental.status = 'rejected'
            rental.save()
            messages.warning(request, f"Rental #{rental.id} rejected.")
        
        elif action == 'start' and rental.status == 'confirmed':
            rental.status = 'active'
            rental.save()
            messages.success(request, f"Rental #{rental.id} marked as active!")
        
        elif action == 'complete' and rental.status == 'active':
            rental.status = 'completed'
            rental.payment_status = True
            rental.payment_date = timezone.now()
            rental.save()
            messages.success(request, f"Rental #{rental.id} completed!")
        
        return redirect('rentals:rentals')

class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'rentals/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner = getattr(self.request.user, 'carowner', None)
        
        if car_owner:
            # Monthly earnings for the last 6 months
            months = []
            earnings = []
            for i in range(5, -1, -1):
                month = timezone.now().replace(day=1) - timedelta(days=30*i)
                next_month = month.replace(day=28) + timedelta(days=4)
                next_month = next_month.replace(day=1)
                
                monthly_earnings = Rental.objects.filter(
                    car__owner=car_owner,
                    created_at__date__gte=month,
                    created_at__date__lt=next_month,
                    payment_status=True
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                months.append(month.strftime('%b %Y'))
                earnings.append(float(monthly_earnings))
            
            context.update({
                'owner': car_owner,
                'months': months,
                'earnings': earnings,
                'total_bookings': Rental.objects.filter(car__owner=car_owner).count(),
                'total_earnings': Rental.objects.filter(
                    car__owner=car_owner, payment_status=True
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
                'popular_car': Car.objects.filter(owner=car_owner).annotate(
                    rental_count=Count('rentals')
                ).order_by('-rental_count').first(),
            })
        
        return context

class OwnerSettingsView(LoginRequiredMixin, UpdateView):
    model = CarOwner
    template_name = 'rentals/owner_settings.html'
    fields = ['company_name', 'verified']
    success_url = reverse_lazy('rentals:owner_dashboard')
    
    def get_object(self):
        car_owner = getattr(self.request.user, 'carowner', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        return car_owner
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)