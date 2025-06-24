from django import forms
from .models import MedicalRecord, VetTask

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['animal', 'diagnosis', 'treatment', 'document']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
        }


class VetTaskForm(forms.ModelForm):
    class Meta:
        model = VetTask
        fields = ['animal', 'title', 'description', 'assigned_to', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }