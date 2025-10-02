from django.views.generic import TemplateView, ListView, CreateView, UpdateView, View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta
import logging

from users.models import CarOwner
from .models import Car, Rental, Review
from .forms import CarForm, RentalForm, ReviewForm, CarSearchForm

logger = logging.getLogger(__name__)

class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'rentals/owner_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        car_owner = getattr(self.request.user, 'owner_profile', None)
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
        recent_rentals = Rental.objects.filter(car__owner=car_owner).select_related('car', 'customer').order_by('-created_at')[:5]
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
        car_owner = getattr(self.request.user, 'owner_profile', None)
        if car_owner:
            return Car.objects.filter(owner=car_owner).select_related('owner')
        return Car.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner = getattr(self.request.user, 'owner_profile', None)
        if car_owner:
            context['stats'] = {
                'total': Car.objects.filter(owner=car_owner).count(),
                'available': Car.objects.filter(owner=car_owner, is_available=True).count(),
                'rented': Car.objects.filter(owner=car_owner, is_available=False).count(),
            }
        return context

class CarCreateView(LoginRequiredMixin, CreateView):
    model = Car
    form_class = CarForm
    template_name = 'rentals/car_form.html'
    success_url = reverse_lazy('rentals:my_cars')
    
    def form_valid(self, form):
        car_owner = getattr(self.request.user, 'owner_profile', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        form.instance.owner = car_owner
        
        messages.success(self.request, f"Car {form.instance.make} {form.instance.model} added successfully!")
        return super().form_valid(form)

class CarUpdateView(LoginRequiredMixin, UpdateView):
    model = Car
    form_class = CarForm
    template_name = 'rentals/car_form.html'
    success_url = reverse_lazy('rentals:my_cars')
    
    def get_queryset(self):
        car_owner = getattr(self.request.user, 'owner_profile', None)
        if car_owner:
            return Car.objects.filter(owner=car_owner)
        return Car.objects.none()
    
    def form_valid(self, form):
        messages.success(self.request, f"Car {form.instance.make} {form.instance.model} updated successfully!")
        return super().form_valid(form)

class CarDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        car = get_object_or_404(Car, pk=pk, owner=request.user.owner_profile)
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
        car_owner = getattr(self.request.user, 'owner_profile', None)
        if car_owner:
            status_filter = self.request.GET.get('status', 'all')
            queryset = Rental.objects.filter(car__owner=car_owner).select_related('car', 'customer')
            
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            
            return queryset.order_by('-created_at')
        return Rental.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner = getattr(self.request.user, 'owner_profile', None)
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
        rental = get_object_or_404(Rental, pk=pk, car__owner=request.user.owner_profile)
        
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
        car_owner = getattr(self.request.user, 'owner_profile', None)
        
        if car_owner:
            # Monthly earnings for the last 6 months
            months = []
            earnings = []
            bookings_data = []
            
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
                
                monthly_bookings = Rental.objects.filter(
                    car__owner=car_owner,
                    created_at__date__gte=month,
                    created_at__date__lt=next_month
                ).count()
                
                months.append(month.strftime('%b %Y'))
                earnings.append(float(monthly_earnings))
                bookings_data.append(monthly_bookings)
            
            # Popular cars
            popular_cars = Car.objects.filter(owner=car_owner).annotate(
                rental_count=Count('rentals'),
                total_earnings=Sum('rentals__total_amount', filter=Q(rentals__payment_status=True))
            ).order_by('-rental_count')[:5]
            
            context.update({
                'owner': car_owner,
                'months': months,
                'earnings': earnings,
                'bookings_data': bookings_data,
                'total_bookings': Rental.objects.filter(car__owner=car_owner).count(),
                'total_earnings': Rental.objects.filter(
                    car__owner=car_owner, payment_status=True
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
                'popular_cars': popular_cars,
                'average_rating': Review.objects.filter(
                    rental__car__owner=car_owner
                ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0,
            })
        
        return context

class OwnerSettingsView(LoginRequiredMixin, UpdateView):
    model = CarOwner
    template_name = 'rentals/owner_settings.html'
    fields = ['company_name', 'company_address', 'tax_id']
    success_url = reverse_lazy('rentals:owner_dashboard')
    
    def get_object(self):
        car_owner = getattr(self.request.user, 'owner_profile', None)
        if not car_owner:
            car_owner = CarOwner.objects.create(user=self.request.user)
        return car_owner
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

# Public car browsing views
class CarBrowseView(ListView):
    """View for customers to browse available cars"""
    model = Car
    template_name = 'rentals/car_browse.html'
    context_object_name = 'cars'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Car.objects.filter(is_available=True, is_active=True)
        
        # Apply filters
        form = CarSearchForm(self.request.GET)
        if form.is_valid():
            car_type = form.cleaned_data.get('car_type')
            fuel_type = form.cleaned_data.get('fuel_type')
            transmission = form.cleaned_data.get('transmission')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            seats = form.cleaned_data.get('seats')
            city = form.cleaned_data.get('city')
            
            if car_type:
                queryset = queryset.filter(car_type=car_type)
            if fuel_type:
                queryset = queryset.filter(fuel_type=fuel_type)
            if transmission:
                queryset = queryset.filter(transmission=transmission)
            if min_price:
                queryset = queryset.filter(daily_rate__gte=min_price)
            if max_price:
                queryset = queryset.filter(daily_rate__lte=max_price)
            if seats:
                queryset = queryset.filter(seats__gte=seats)
            if city:
                queryset = queryset.filter(city__icontains=city)
        
        return queryset.select_related('owner').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = CarSearchForm(self.request.GET)
        context['car_types'] = Car.CAR_TYPES
        return context

class CarDetailView(DetailView):
    """View for car details"""
    model = Car
    template_name = 'rentals/car_detail.html'
    context_object_name = 'car'
    
    def get_queryset(self):
        return Car.objects.filter(is_available=True, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['similar_cars'] = Car.objects.filter(
            car_type=self.object.car_type,
            is_available=True,
            is_active=True
        ).exclude(pk=self.object.pk)[:4]
        context['reviews'] = Review.objects.filter(
            rental__car=self.object,
            rental__status='completed'
        ).select_related('rental__customer')[:10]
        return context

class CarAvailabilityCheckView(View):
    """API endpoint to check car availability"""
    
    def get(self, request, car_id):
        try:
            car = get_object_or_404(Car, id=car_id, is_available=True, is_active=True)
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not start_date or not end_date:
                return JsonResponse({'error': 'Start and end dates are required'}, status=400)
            
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Check availability
            is_available = not Rental.objects.filter(
                car=car,
                status__in=['pending', 'confirmed', 'active'],
                start_date__lt=end_date,
                end_date__gt=start_date
            ).exists()
            
            # Calculate total amount
            total_days = (end_date - start_date).days
            total_amount = total_days * car.daily_rate if total_days > 0 else 0
            
            return JsonResponse({
                'available': is_available,
                'total_days': total_days,
                'total_amount': float(total_amount),
                'daily_rate': float(car.daily_rate),
                'car_name': f"{car.make} {car.model}"
            })
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return JsonResponse({'error': 'Invalid request'}, status=400)