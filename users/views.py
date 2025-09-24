from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import SignUpForm

class HomeView(TemplateView):
    template_name = 'users/home.html'  # Added 'users/' prefix

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'users/signup.html'  # Added 'users/' prefix
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        messages.success(self.request, "Account created successfully! Please log in.")
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        if self.request.user.account_type == 'customer':
            return reverse_lazy('users:customer_dashboard')
        return reverse_lazy('users:owner_dashboard')

class CustomLogoutView(LogoutView):
    next_page = 'users:home'
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)

class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/customer_dashboard.html'  # Added 'users/' prefix
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = getattr(self.request.user, 'customer', None)
        return context

class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/owner_dashboard.html'  # Added 'users/' prefix
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owner'] = getattr(self.request.user, 'rentalowner', None)
        return context