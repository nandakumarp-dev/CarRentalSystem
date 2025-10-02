from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, BookingReview, FavoriteCar

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'pickup_location', 'dropoff_location', 'special_requests']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date() + timezone.timedelta(days=1)
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date() + timezone.timedelta(days=2)
            }),
            'pickup_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter pickup location'
            }),
            'dropoff_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter dropoff location (optional)'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Any special requirements or requests...'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date.")
            
            if start_date < timezone.now().date():
                raise ValidationError("Start date cannot be in the past.")
            
            # Check if rental period is reasonable
            max_rental_days = 90
            rental_days = (end_date - start_date).days
            if rental_days > max_rental_days:
                raise ValidationError(f"Rental period cannot exceed {max_rental_days} days.")
            if rental_days < 1:
                raise ValidationError("Rental period must be at least 1 day.")
        
        return cleaned_data

class BookingReviewForm(forms.ModelForm):
    class Meta:
        model = BookingReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-control',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience with this rental...'
            }),
        }
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating not in [1, 2, 3, 4, 5]:
            raise ValidationError("Please select a valid rating.")
        return rating

class BookingFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class PaymentForm(forms.Form):
    """Form for payment processing (simplified for example)"""
    card_number = forms.CharField(
        max_length=16,
        min_length=16,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'pattern': '[0-9]{16}'
        })
    )
    expiry_date = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'pattern': '(0[1-9]|1[0-2])\/[0-9]{2}'
        })
    )
    cvv = forms.CharField(
        max_length=3,
        min_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'pattern': '[0-9]{3}'
        })
    )
    card_holder = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Card Holder Name'
        })
    )