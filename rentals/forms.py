from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Car, Rental, Review

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'make', 'model', 'year', 'car_type', 'fuel_type', 'transmission',
            'daily_rate', 'seats', 'color', 'license_plate', 'mileage',
            'pickup_location', 'city', 'description', 'image', 'features'
        ]
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '1990', 'max': '2025'}),
            'car_type': forms.Select(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-control'}),
            'transmission': forms.Select(attrs={'class': 'form-control'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_license_plate(self):
        license_plate = self.cleaned_data.get('license_plate')
        if Car.objects.filter(license_plate=license_plate).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A car with this license plate already exists.")
        return license_plate
    
    def clean_year(self):
        year = self.cleaned_data.get('year')
        current_year = timezone.now().year
        if year < 1990 or year > current_year + 1:
            raise ValidationError(f"Year must be between 1990 and {current_year + 1}.")
        return year

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['start_date', 'end_date', 'pickup_location', 'dropoff_location', 'special_requests']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control'}),
            'dropoff_location': forms.TextInput(attrs={'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
            
            # Check if rental period is reasonable (e.g., not more than 90 days)
            max_rental_days = 90
            if (end_date - start_date).days > max_rental_days:
                raise ValidationError(f"Rental period cannot exceed {max_rental_days} days.")
        
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience...'}),
        }

class CarSearchForm(forms.Form):
    car_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Car.CAR_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fuel_type = forms.ChoiceField(
        choices=[('', 'All Fuel Types')] + Car.FUEL_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    transmission = forms.ChoiceField(
        choices=[('', 'All Transmissions')] + Car.TRANSMISSION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=1000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min price'})
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=1000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max price'})
    )
    seats = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min seats'})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )