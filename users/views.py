from django.shortcuts import render
from django.views import View

# Create your views here.

class UsersDashboard(View):

    def get(self, request, *args, **kwargs):

        return render (request,'usersdashboard.html')
    
class RentalOwnerView(View):

    def get(self, request, *args, **kwargs):

        return render (request,'rentalownersdashboard.html')

class SuperAdminView(View):

    def get(self, request, *args, **kwargs):

        return render (request,'superadmindashboard.html')
    
class LoginView(View):

    def get(self, request,*args, **kwargs):

        return render(request, 'login.html')
    
class SignUpView(View):

    def get(self, request,*args, **kwargs):

        return render(request, 'signup.html')
    
class WelcomePageView(View):

    def get(self, request,*args, **kwargs):

        return render(request, 'welcomepage.html')