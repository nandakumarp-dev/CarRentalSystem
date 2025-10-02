from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied, ValidationError
from datetime import datetime, timedelta
import logging

from .models import Booking, BookingReview
from rentals.models import Car

logger = logging.getLogger(__name__)


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    """Production-ready customer dashboard with comprehensive analytics"""
    template_name = 'bookings/customer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            # Booking statistics with optimized queries
            bookings = Booking.objects.filter(customer=user)
            
            # Use select_related and prefetch_related for performance
            recent_bookings = bookings.select_related('car', 'payment').order_by('-created_at')[:5]
            
            # Calculate stats in a single query where possible
            status_counts = bookings.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status__in=['confirmed', 'active'])),
                completed=Count('id', filter=Q(status='completed')),
                upcoming=Count('id', filter=Q(status='confirmed', start_date__gt=timezone.now().date())),
            )
            
            # Loyalty points calculation
            loyalty_points = status_counts['completed'] * 100
            
            # Recommended cars with business logic
            recommended_cars = self.get_recommended_cars(user)
            
            context.update({
                'active_bookings_count': status_counts['active'],
                'total_bookings_count': status_counts['total'],
                'completed_bookings_count': status_counts['completed'],
                'upcoming_bookings_count': status_counts['upcoming'],
                'recent_bookings': recent_bookings,
                'loyalty_points': loyalty_points,
                'recommended_cars': recommended_cars,
            })
            
        except Exception as e:
            logger.error(f"Error in CustomerDashboardView: {str(e)}")
            messages.error(self.request, "Unable to load dashboard data. Please try again.")
            
        return context
    
    def get_recommended_cars(self, user):
        """Get personalized car recommendations"""
        try:
            # Base queryset
            cars = Car.objects.filter(is_available=True)
            
            # If user has previous bookings, recommend similar cars
            user_bookings = Booking.objects.filter(customer=user, status='completed')
            if user_bookings.exists():
                # Get most booked car type by user
                favorite_type = user_bookings.values('car__car_type').annotate(
                    count=Count('id')
                ).order_by('-count').first()
                
                if favorite_type:
                    cars = cars.filter(car_type=favorite_type['car__car_type'])
            
            # Add popular cars as fallback
            popular_cars = cars.annotate(
                booking_count=Count('bookings')
            ).order_by('-booking_count')[:3]
            
            return popular_cars
            
        except Exception as e:
            logger.error(f"Error getting recommended cars: {str(e)}")
            return Car.objects.filter(is_available=True)[:3]


class BookingListView(LoginRequiredMixin, ListView):
    """View for listing all customer bookings with filtering and pagination"""
    model = Booking
    template_name = 'bookings/my_bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Booking.objects.filter(
            customer=self.request.user
        ).select_related('car', 'payment').order_by('-created_at')
        
        # Apply status filter
        status_filter = self.request.GET.get('status')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', 'all')
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single booking"""
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        # Ensure users can only see their own bookings
        return Booking.objects.filter(customer=self.request.user).select_related(
            'car', 'payment', 'review'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        # Add related data
        context['can_review'] = (
            booking.status == 'completed' and 
            not hasattr(booking, 'review')
        )
        context['can_cancel'] = booking.can_be_cancelled
        
        return context


class BookingCreateView(LoginRequiredMixin, CreateView):
    """View for creating new bookings with validation"""
    model = Booking
    template_name = 'bookings/create_booking.html'
    fields = ['start_date', 'end_date', 'pickup_location', 'special_requests']
    
    def dispatch(self, request, *args, **kwargs):
        self.car = get_object_or_404(Car, id=kwargs['car_id'], is_available=True)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['car'] = self.car
        context['min_date'] = timezone.now().date() + timedelta(days=1)
        return context
    
    def form_valid(self, form):
        try:
            form.instance.customer = self.request.user
            form.instance.car = self.car
            
            # Validate dates
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            if start_date >= end_date:
                form.add_error('end_date', 'End date must be after start date')
                return self.form_invalid(form)
            
            if start_date < timezone.now().date():
                form.add_error('start_date', 'Start date cannot be in the past')
                return self.form_invalid(form)
            
            # Check car availability for the selected dates
            if not self.is_car_available(start_date, end_date):
                form.add_error(None, 'Car is not available for the selected dates')
                return self.form_invalid(form)
            
            # Calculate total amount
            total_days = (end_date - start_date).days
            form.instance.total_days = total_days
            form.instance.total_amount = total_days * self.car.daily_rate
            
            response = super().form_valid(form)
            
            messages.success(
                self.request, 
                f'Booking created successfully! Please proceed to payment.'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            messages.error(self.request, 'An error occurred while creating the booking.')
            return self.form_invalid(form)
    
    def is_car_available(self, start_date, end_date):
        """Check if car is available for the given date range"""
        conflicting_bookings = Booking.objects.filter(
            car=self.car,
            status__in=['pending', 'confirmed', 'active'],
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        return not conflicting_bookings.exists()
    
    def get_success_url(self):
        return reverse('bookings:booking_payment', kwargs={'pk': self.object.pk})


class BookingCancelView(LoginRequiredMixin, View):
    """View for cancelling bookings with proper business logic"""
    
    def post(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.filter(customer=request.user),
            pk=pk
        )
        
        try:
            if not booking.can_be_cancelled:
                messages.error(request, 'This booking cannot be cancelled.')
                return redirect('bookings:my_bookings')
            
            # Store old status for messaging
            old_status = booking.status
            
            # Update booking status
            booking.status = 'cancelled'
            
            # Handle refund logic if payment was made
            if booking.payment_status == 'paid':
                booking.payment_status = 'refunded'
                # Here you would integrate with your payment provider's refund API
                # For now, we'll just log it
                logger.info(f"Refund required for booking #{booking.id}")
            
            booking.save()
            
            messages.success(
                request, 
                f'Booking #{booking.id} has been cancelled successfully.'
            )
            
            # Send notification (you can integrate with Celery for async processing)
            self.send_cancellation_notification(booking, old_status)
            
        except Exception as e:
            logger.error(f"Error cancelling booking #{pk}: {str(e)}")
            messages.error(request, 'An error occurred while cancelling the booking.')
        
        return redirect('bookings:my_bookings')
    
    def send_cancellation_notification(self, booking, old_status):
        """Send cancellation notification (to be implemented with Celery)"""
        # This would typically send emails, push notifications, etc.
        logger.info(f"Booking #{booking.id} cancelled. Previous status: {old_status}")


class RentalHistoryView(LoginRequiredMixin, ListView):
    """View for completed rentals with review functionality"""
    model = Booking
    template_name = 'bookings/rental_history.html'
    context_object_name = 'completed_bookings'
    paginate_by = 10
    
    def get_queryset(self):
        return Booking.objects.filter(
            customer=self.request.user,
            status='completed'
        ).select_related('car', 'review').order_by('-created_at')


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """View for creating reviews for completed bookings"""
    model = BookingReview
    template_name = 'bookings/create_review.html'
    fields = ['rating', 'comment']
    
    def dispatch(self, request, *args, **kwargs):
        self.booking = get_object_or_404(
            Booking.objects.filter(customer=request.user, status='completed'),
            pk=kwargs['booking_id']
        )
        
        # Check if review already exists
        if hasattr(self.booking, 'review'):
            raise Http404("Review already exists for this booking.")
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking'] = self.booking
        return context
    
    def form_valid(self, form):
        form.instance.booking = self.booking
        response = super().form_valid(form)
        messages.success(self.request, 'Thank you for your review!')
        return response
    
    def get_success_url(self):
        return reverse('bookings:rental_history')


class BookingPaymentView(LoginRequiredMixin, DetailView):
    """View for handling booking payments"""
    model = Booking
    template_name = 'bookings/booking_payment.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        return Booking.objects.filter(customer=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add payment gateway context (Stripe, PayPal keys, etc.)
        context['stripe_public_key'] = 'your_stripe_public_key'  # Should be in settings
        return context


class BookingAvailabilityCheckView(LoginRequiredMixin, View):
    """API endpoint to check car availability"""
    
    def get(self, request, car_id):
        try:
            car = get_object_or_404(Car, id=car_id)
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not start_date or not end_date:
                return JsonResponse({'error': 'Start and end dates are required'}, status=400)
            
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Check availability
            is_available = not Booking.objects.filter(
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
                'daily_rate': float(car.daily_rate)
            })
            
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return JsonResponse({'error': 'Invalid request'}, status=400)