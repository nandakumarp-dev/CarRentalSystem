from django.urls import path

from . import views 

urlpatterns = [  

    path('usersdashboard/', views.UsersDashboard.as_view(),name='usersdashboard'),
    path('rentalownersdashboard/', views.RentalOwnerView.as_view(),name='rentalownersdashboard'),
    path('superadmindashboard/', views.SuperAdminView.as_view(),name='superadmindashboard'),
    path('login/', views.LoginView.as_view(),name='login'),
    path('signup/', views.SignUpView.as_view(),name='signup'),
    path('', views.WelcomePageView.as_view(),name='welcomepage'),

]