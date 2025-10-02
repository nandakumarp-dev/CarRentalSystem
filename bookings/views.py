from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import logging
import json

from .models import Booking, BookingReview, FavoriteCar
from rentals.models import Car, Rental
from .forms import BookingForm, BookingReviewForm, BookingFilterForm, PaymentForm

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
            
            # Use select_related for performance
            recent_bookings = bookings.select_related('car', 'car__owner').order_by('-created_at')[:5]
            
            # Calculate stats in a single query where possible
            status_counts = bookings.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status__in=['confirmed', 'active'])),
                completed=Count('id', filter=Q(status='completed')),
                upcoming=Count('id', filter=Q(status='confirmed', start_date__gt=timezone.now().date())),
            )
            
            # Loyalty points calculation (more sophisticated)
            completed_bookings = status_counts['completed']
            loyalty_points = completed_bookings * 100
            # Bonus points for frequent rentals
            if completed_bookings >= 10:
                loyalty_points += 500  # Gold member bonus
            elif completed_bookings >= 5:
                loyalty_points += 200  # Silver member bonus
            
            # Recommended cars with business logic
            recommended_cars = self.get_recommended_cars(user)
            
            # Favorite cars count
            favorite_cars_count = FavoriteCar.objects.filter(customer=user).count()
            
            context.update({
                'active_bookings_count': status_counts['active'],
                'total_bookings_count': status_counts['total'],
                'completed_bookings_count': status_counts['completed'],
                'upcoming_bookings_count': status_counts['upcoming'],
                'recent_bookings': recent_bookings,
                'loyalty_points': loyalty_points,
                'recommended_cars': recommended_cars,
                'favorite_cars_count': favorite_cars_count,
                'member_tier': self.get_member_tier(completed_bookings),
            })
            
        except Exception as e:
            logger.error(f"Error in CustomerDashboardView: {str(e)}")
            messages.error(self.request, "Unable to load dashboard data. Please try again.")
            
        return context
    
    def get_recommended_cars(self, user):
        """Get personalized car recommendations"""
        try:
            # Base queryset - available cars
            cars = Car.objects.filter(is_available=True, is_active=True)
            
            # If user has previous bookings, recommend similar cars
            user_bookings = Booking.objects.filter(customer=user, status='completed')
            if user_bookings.exists():
                # Get most booked car type by user
                favorite_type = user_bookings.values('car__car_type').annotate(
                    count=Count('id')
                ).order_by('-count').first()
                
                if favorite_type:
                    cars = cars.filter(car_type=favorite_type['car__car_type'])
            
            # Add highly rated cars as fallback
            popular_cars = cars.annotate(
                avg_rating=Avg('rentals__review__rating', filter=Q(rentals__status='completed')),
                booking_count=Count('bookings')
            ).filter(
                Q(avg_rating__gte=4) | Q(booking_count__gte=1)
            ).order_by('-avg_rating', '-booking_count')[:6]
            
            return popular_cars
            
        except Exception as e:
            logger.error(f"Error getting recommended cars: {str(e)}")
            return Car.objects.filter(is_available=True, is_active=True)[:6]
    
    def get_member_tier(self, completed_bookings):
        """Determine customer membership tier"""
        if completed_bookings >= 10:
            return 'gold'
        elif completed_bookings >= 5:
            return 'silver'
        elif completed_bookings >= 1:
            return 'bronze'
        else:
            return 'new'


class BookingListView(LoginRequiredMixin, ListView):
    """View for listing all customer bookings with filtering and pagination"""
    model = Booking
    template_name = 'bookings/my_bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Booking.objects.filter(
            customer=self.request.user
        ).select_related('car', 'car__owner').order_by('-created_at')
        
        # Apply filters
        form = BookingFilterForm(self.request.GET)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if status:
                queryset = queryset.filter(status=status)
            if date_from:
                queryset = queryset.filter(start_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(end_date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = BookingFilterForm(self.request.GET)
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single booking"""
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        # Ensure users can only see their own bookings
        return Booking.objects.filter(customer=self.request.user).select_related(
            'car', 'car__owner', 'payment', 'review'
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
        context['is_overdue'] = booking.is_overdue
        
        return context


class BookingCreateView(LoginRequiredMixin, CreateView):
    """View for creating new bookings with validation"""
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/create_booking.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.car = get_object_or_404(
            Car, 
            id=kwargs['car_id'], 
            is_available=True, 
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['car'] = self.car
        context['min_date'] = timezone.now().date() + timedelta(days=1)
        context['max_date'] = timezone.now().date() + timedelta(days=90)
        return context
    
    def form_valid(self, form):
        try:
            form.instance.customer = self.request.user
            form.instance.car = self.car
            
            # Validate dates
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Check car availability for the selected dates
            if not self.is_car_available(start_date, end_date):
                form.add_error(None, 'Car is not available for the selected dates. Please choose different dates.')
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
            
            # Log booking creation
            logger.info(f"Booking #{self.object.id} created for car #{self.car.id} by user {self.request.user.username}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            messages.error(self.request, 'An error occurred while creating the booking. Please try again.')
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
                logger.info(f"Refund processed for booking #{booking.id}")
            
            booking.save()
            
            messages.success(
                request, 
                f'Booking #{booking.id} has been cancelled successfully.'
            )
            
            # Log cancellation
            logger.info(f"Booking #{booking.id} cancelled by user {request.user.username}. Previous status: {old_status}")
            
        except Exception as e:
            logger.error(f"Error cancelling booking #{pk}: {str(e)}")
            messages.error(request, 'An error occurred while cancelling the booking.')
        
        return redirect('bookings:my_bookings')


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
        ).select_related('car', 'car__owner', 'review').order_by('-created_at')


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """View for creating reviews for completed bookings"""
    model = BookingReview
    form_class = BookingReviewForm
    template_name = 'bookings/create_review.html'
    
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
        
        # Log review creation
        logger.info(f"Review created for booking #{self.booking.id} by user {self.request.user.username}")
        
        return response
    
    def get_success_url(self):
        return reverse('bookings:rental_history')


class BookingPaymentView(LoginRequiredMixin, DetailView):
    """View for handling booking payments"""
    model = Booking
    template_name = 'bookings/booking_payment.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        return Booking.objects.filter(customer=self.request.user, status='pending')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_form'] = PaymentForm()
        # Add payment gateway context (Stripe, PayPal keys, etc.)
        context['stripe_public_key'] = 'pk_test_your_stripe_public_key'  # Should be in settings
        return context


class ProcessPaymentView(LoginRequiredMixin, View):
    """View to process payment for a booking"""
    
    def post(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.filter(customer=request.user, status='pending'),
            pk=pk
        )
        
        try:
            # In a real application, you would integrate with Stripe, PayPal, etc.
            # This is a simplified example
            
            form = PaymentForm(request.POST)
            if form.is_valid():
                # Simulate payment processing
                # In production, you would:
                # 1. Create payment intent with Stripe
                # 2. Confirm payment
                # 3. Handle webhooks for payment confirmation
                
                # For demo purposes, we'll just mark as paid
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
                booking.save()
                
                # Create payment record
                from .models import BookingPayment
                BookingPayment.objects.create(
                    booking=booking,
                    amount=booking.total_amount,
                    payment_method='card',
                    paid_at=timezone.now()
                )
                
                messages.success(request, 'Payment processed successfully! Your booking is now confirmed.')
                logger.info(f"Payment processed for booking #{booking.id}")
                
                return redirect('bookings:booking_detail', pk=booking.id)
            else:
                messages.error(request, 'Please check your payment information and try again.')
                return redirect('bookings:booking_payment', pk=booking.id)
                
        except Exception as e:
            logger.error(f"Error processing payment for booking #{pk}: {str(e)}")
            messages.error(request, 'An error occurred while processing your payment. Please try again.')
            return redirect('bookings:booking_payment', pk=booking.id)


class FavoriteCarView(LoginRequiredMixin, View):
    """View to add/remove cars from favorites"""
    
    def post(self, request, car_id):
        car = get_object_or_404(Car, id=car_id, is_active=True)
        favorite, created = FavoriteCar.objects.get_or_create(
            customer=request.user,
            car=car
        )
        
        if created:
            messages.success(request, f'{car.make} {car.model} added to favorites!')
        else:
            favorite.delete()
            messages.info(request, f'{car.make} {car.model} removed from favorites.')
        
        return redirect('rentals:car_detail', pk=car_id)


class FavoriteListView(LoginRequiredMixin, ListView):
    """View to show user's favorite cars"""
    model = FavoriteCar
    template_name = 'bookings/favorite_cars.html'
    context_object_name = 'favorites'
    paginate_by = 12
    
    def get_queryset(self):
        return FavoriteCar.objects.filter(
            customer=self.request.user
        ).select_related('car', 'car__owner').order_by('-created_at')


class BookingAvailabilityCheckView(LoginRequiredMixin, View):
    """API endpoint to check car availability and calculate price"""
    
    def get(self, request, car_id):
        try:
            car = get_object_or_404(Car, id=car_id, is_active=True)
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            if not start_date or not end_date:
                return JsonResponse({'error': 'Start and end dates are required'}, status=400)
            
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Validate dates
            if start_date >= end_date:
                return JsonResponse({'error': 'End date must be after start date'}, status=400)
            
            if start_date < timezone.now().date():
                return JsonResponse({'error': 'Start date cannot be in the past'}, status=400)
            
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
            
            # Calculate any discounts
            discount = self.calculate_discount(total_days, request.user)
            final_amount = total_amount - discount
            
            return JsonResponse({
                'available': is_available,
                'total_days': total_days,
                'total_amount': float(total_amount),
                'discount': float(discount),
                'final_amount': float(final_amount),
                'daily_rate': float(car.daily_rate),
                'car_name': f"{car.make} {car.model}"
            })
            
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return JsonResponse({'error': 'Invalid request'}, status=400)
    
    def calculate_discount(self, total_days, user):
        """Calculate discount based on rental duration and user loyalty"""
        discount = 0
        
        # Long-term rental discount
        if total_days >= 7:
            discount += (total_days * user.car.daily_rate) * 0.1  # 10% off for 7+ days
        elif total_days >= 3:
            discount += (total_days * user.car.daily_rate) * 0.05  # 5% off for 3-6 days
        
        # Loyalty discount based on completed bookings
        completed_bookings = Booking.objects.filter(customer=user, status='completed').count()
        if completed_bookings >= 5:
            discount += (total_days * user.car.daily_rate) * 0.05  # Additional 5% for loyal customers
        
        return discount


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    """Webhook endpoint for payment providers (Stripe, etc.)"""
    
    def post(self, request):
        try:
            # In production, you would verify the webhook signature
            payload = json.loads(request.body)
            
            # Process different webhook events
            event_type = payload.get('type')
            
            if event_type == 'payment_intent.succeeded':
                payment_intent = payload.get('data', {}).get('object', {})
                payment_intent_id = payment_intent.get('id')
                
                # Find and update the corresponding booking
                try:
                    from .models import BookingPayment
                    booking_payment = BookingPayment.objects.get(
                        payment_intent_id=payment_intent_id
                    )
                    booking = booking_payment.booking
                    booking.payment_status = 'paid'
                    booking.status = 'confirmed'
                    booking.save()
                    
                    booking_payment.paid_at = timezone.now()
                    booking_payment.save()
                    
                    logger.info(f"Payment confirmed via webhook for booking #{booking.id}")
                    
                except BookingPayment.DoesNotExist:
                    logger.error(f"Payment intent not found: {payment_intent_id}")
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return JsonResponse({'error': 'Webhook processing failed'}, status=400)