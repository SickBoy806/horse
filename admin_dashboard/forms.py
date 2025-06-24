from django import forms
from accounts.models import CustomUser
from core.models import Task
from .models import VetTask, MedicalRecord  # ✅ FIXED

class CreateUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'branch', 'password']

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
        fields = ['animal', 'title', 'description', 'assigned_to', 'due_date']
