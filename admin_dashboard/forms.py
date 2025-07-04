from django import forms
from accounts.models import CustomUser
from core.models import Task
from .models import VetTask, MedicalRecord  # ✅ FIXED
from core.models import SupportTicket
from core.models import SupportTicket, TicketReply

 # or correct import path if it's in another app



class CustomUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'role', 'branch', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])  # hash the password
        if commit:
            user.save()
        return user

class AssignTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['animal', 'diagnosis', 'treatment', 'document']
        # widgets = {
        #     'diagnosis': forms.Textarea(attrs={'rows': 3}),
        #     'treatment': forms.Textarea(attrs={'rows': 3}),
        # }

class VetTaskForm(forms.ModelForm):
    class Meta:
        model = VetTask
        fields = ['title', 'description', 'assigned_to', 'priority', 'deadline']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def _init_(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super()._init_(*args, **kwargs)
        if branch:
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(branch=branch, role__in=['user', 'veterinarian'])

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket  # <-- Make sure this model exists and is imported
        fields = ['subject', 'description']  # Adjust as needed

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply  # <-- Make sure this model exists and is imported
        fields = ['message']

