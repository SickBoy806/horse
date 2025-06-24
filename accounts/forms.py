from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, ROLES, BRANCHES

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLES)
    branch = forms.ChoiceField(choices=BRANCHES)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'branch', 'password1', 'password2']
