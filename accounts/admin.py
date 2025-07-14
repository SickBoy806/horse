from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

from .models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'branch')  # changed here

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ('username', 'email', 'role', 'branch', 'is_staff', 'is_active')  # changed here
    list_filter = ('role', 'branch', 'is_staff')  # changed here

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'branch')}),  # changed here
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'branch', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)


admin.site.register(CustomUser, CustomUserAdmin)
