from django.views.generic import TemplateView, CreateView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
from .forms import SignUpForm, CustomLoginForm, UserUpdateForm, CustomerProfileForm, CarOwnerProfileForm
from .models import Customer, CarOwner
from django.views.generic import TemplateView
from rentals.models import Car

class HomeView(TemplateView):
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available cars (limit to 6 for the homepage)
        available_cars = Car.objects.filter(
            is_available=True, 
            is_active=True
        ).select_related('owner')[:6]
        
        # Add cars and statistics to context
        context.update({
            'cars': available_cars,
            'total_cars': Car.objects.filter(is_available=True, is_active=True).count(),
            'total_rentals': 2500,  # You can replace this with actual count if you have rental data
        })
        
        return context

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        messages.success(self.request, "Account created successfully! Please log in.")
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = CustomLoginForm
    
    def get_success_url(self):
        if self.request.user.account_type == 'customer':
            return reverse_lazy('bookings:customer_dashboard')
        return reverse_lazy('rentals:owner_dashboard')

class CustomLogoutView(LogoutView):
    next_page = 'users:home'
    
    def dispatch(self, request, *args, **kwargs):
        username = request.user.username
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, f"You have been successfully logged out. Goodbye, {username}!")
        return response

class ProfileUpdateView(LoginRequiredMixin, FormView):
    template_name = 'users/profile_update.html'
    success_url = reverse_lazy('users:profile_update')
    
    def get_form_class(self):
        if self.request.user.account_type == 'customer':
            return CustomerProfileForm
        return CarOwnerProfileForm
    
    def get_form(self, form_class=None):
        if self.request.user.account_type == 'customer':
            profile, created = Customer.objects.get_or_create(user=self.request.user)
            return CustomerProfileForm(instance=profile, **self.get_form_kwargs())
        else:
            profile, created = CarOwner.objects.get_or_create(user=self.request.user)
            return CarOwnerProfileForm(instance=profile, **self.get_form_kwargs())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserUpdateForm(instance=self.request.user)
        return context
    
    def form_valid(self, form):
        user_form = UserUpdateForm(self.request.POST, instance=self.request.user)
        
        with transaction.atomic():
            if user_form.is_valid():
                user_form.save()
            form.save()
        
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    template_name = 'users/user_update.html'
    success_url = reverse_lazy('users:profile_update')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, "User information updated successfully!")
        return super().form_valid(form)