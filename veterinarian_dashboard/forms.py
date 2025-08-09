from django import forms
from core.models import (
    Animal, Message, MedicalRecord, VetTask, 
    EquipmentLog, EmergencyIncident
)
from accounts.models import CustomUser

REPORT_TYPE_CHOICES = [
    ('breeding', 'Breeding'),
    ('lab_diagnosis', 'Lab Diagnosis'),
    ('deworming', 'Deworming'),
    ('postmortem', 'Postmortem'),
    ('transfer', 'Transfer'),
    ('referral', 'Referral'),
    ('dipping', 'Dipping'),
    ('vaccination', 'Vaccination'),
    ('checkup', 'Routine Checkup'),
    ('surgery', 'Surgery'),
]

class MedicalRecordForm(forms.ModelForm):
    report_type = forms.ChoiceField(choices=REPORT_TYPE_CHOICES)
    animal = forms.ModelChoiceField(queryset=Animal.objects.none(), label="Animal")

    class Meta:
        model = MedicalRecord
        fields = [
            'report_type', 'animal', 'diagnosis', 'treatment', 'document',
            'weight', 'temperature',
            'mating_date', 'expected_delivery_date', 'breeding_method',
            'lab_test_name', 'test_result', 'sample_type',
            'dewormer_name', 'next_deworming_date',
            'cause_of_death', 'postmortem_findings',
            'transfer_from', 'transfer_to', 'reason_for_transfer',
            'referred_to', 'referral_reason',
            'dip_type', 'dipping_location',
            'surgery_type', 'anesthesia_used',
            'vaccine_name', 'next_due_date',
        ]
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'test_result': forms.Textarea(attrs={'rows': 3}),
            'postmortem_findings': forms.Textarea(attrs={'rows': 3}),
            'reason_for_transfer': forms.Textarea(attrs={'rows': 3}),
            'referral_reason': forms.Textarea(attrs={'rows': 3}),
            'cause_of_death': forms.Textarea(attrs={'rows': 3}),
            'mating_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'next_deworming_date': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
            'weight': forms.NumberInput(attrs={'step': '0.01'}),
            'temperature': forms.NumberInput(attrs={'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        # Pop custom kwargs before passing to parent class
        user = kwargs.pop('user', None)
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)

        # Filter animals by branch
        if branch:
            self.fields['animal'].queryset = Animal.objects.filter(branch=branch)


class VetTaskForm(forms.ModelForm):
    class Meta:
        model = VetTask
        fields = ['animal', 'title', 'description', 'assigned_to', 'priority', 'due_date', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Filter animals and users by branch
            self.fields['animal'].queryset = Animal.objects.filter(branch=user.branch)
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                branch=user.branch,
                role__in=['user', 'staff', 'veterinarian']
            )


# Create a simple Patient form using Animal model
class PatientForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['name', 'species', 'breed', 'age', 'date_of_birth', 'owner_name']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'age': forms.NumberInput(attrs={'step': '0.01'}),
        }


class EmergencyReportForm(forms.ModelForm):
    class Meta:
        model = EmergencyIncident
        fields = ['animal', 'incident_type', 'severity', 'description', 'photo', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the emergency in detail...'}),
            'location': forms.TextInput(attrs={'placeholder': 'Location of the incident'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Filter animals by branch
            self.fields['animal'].queryset = Animal.objects.filter(branch=user.branch)
        else:
            # If no user or branch, show all animals (fallback)
            self.fields['animal'].queryset = Animal.objects.all()


class EquipmentLogForm(forms.ModelForm):
    class Meta:
        model = EquipmentLog
        fields = ['equipment', 'action', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes (optional)'}),
        }
