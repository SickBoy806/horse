from django import forms
from accounts.models import CustomUser
from core.models import Branch

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'branch', 'password']
        widgets = {
            'role': forms.Select(choices=CustomUser._meta.get_field('role').choices),
            'branch': forms.Select(choices=CustomUser._meta.get_field('branch').choices),
            'password': forms.PasswordInput(render_value=True),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash password before saving
        raw_password = self.cleaned_data.get('password')
        if raw_password:
            user.set_password(raw_password)
        if commit:
            user.save()
        return user


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'location', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Branch Name'}),
            'location': forms.TextInput(attrs={'placeholder': 'Branch Location'}),
            'is_active': forms.CheckboxInput(),
        }


