from django import forms
from .models import AnimalLog
from .models import DailyActivityReport
from .models import UserMessage
from .models import EmergencyIncident
from .models import EquipmentLog
from .models import SupportRequest




class AnimalLogForm(forms.ModelForm):
    class Meta:
        model = AnimalLog
        fields = ['animal', 'activity_type', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border rounded px-3 py-2'}),
            'animal': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'activity_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
        }

class DailyActivityReportForm(forms.ModelForm):
    class Meta:
        model = DailyActivityReport
        fields = ['summary', 'issues_faced', 'hours_worked']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border rounded px-3 py-2'}),
            'issues_faced': forms.Textarea(attrs={'rows': 3, 'class': 'w-full border rounded px-3 py-2'}),
            'hours_worked': forms.NumberInput(attrs={'step': 0.5, 'class': 'w-full border rounded px-3 py-2'}),
        }

class UserMessageForm(forms.ModelForm):
    class Meta:
        model = UserMessage
        fields = ['receiver', 'subject', 'body']
        widgets = {
            'receiver': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'subject': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'body': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border rounded px-3 py-2'}),
        }

class EmergencyIncidentForm(forms.ModelForm):
    class Meta:
        model = EmergencyIncident
        fields = ['animal', 'incident_type', 'description', 'photo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border rounded px-3 py-2'}),
            'animal': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'incident_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'w-full'}),
        }

class EquipmentLogForm(forms.ModelForm):
    class Meta:
        model = EquipmentLog
        fields = ['equipment', 'action', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'w-full border rounded'}),
        }

class SupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ['subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'w-full border rounded'}),
        }