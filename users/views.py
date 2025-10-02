# source users/views.py

from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import SignUpForm

class HomeView(TemplateView):
    template_name = 'users/home.html'

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        messages.success(self.request, "Account created successfully! Please log in.")
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        if self.request.user.account_type == 'customer':
            return reverse_lazy('users:customer_dashboard')
        return reverse_lazy('rentals:owner_dashboard')  # Changed to rentals app

class CustomLogoutView(LogoutView):
    next_page = 'users:home'
    
    def dispatch(self, request, *args, **kwargs):
        username = request.user.username
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, f"You have been successfully logged out. Goodbye, {username}!")
        return response

class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/customer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = getattr(self.request.user, 'customer', None)
        return context
