# source users/forms.py 

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Customer, CarOwner

class SignUpForm(UserCreationForm):
    account_type = forms.ChoiceField(choices=User.ACCOUNT_TYPES)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'account_type', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.account_type = self.cleaned_data['account_type']
        
        if commit:
            user.save()
            if user.account_type == 'customer':
                Customer.objects.create(user=user)
            else:
                CarOwner.objects.create(user=user)
        return user