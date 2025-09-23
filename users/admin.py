from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from .models import Profile

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(UserAdmin):

    list_display = ('username','email','first_name','last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')




