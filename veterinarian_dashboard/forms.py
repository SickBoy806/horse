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
    SPECIES_CHOICES = [
        ('Dog', 'Dog'),
        ('Horse', 'Horse'),
    ]

    DOG_BREEDS = [
        ('labrador', 'Labrador Retriever'),
        ('germanshepherd', 'German Shepherd'),
        ('bulldog', 'Bulldog'),
        # add more dog breeds here
    ]

    HORSE_BREEDS = [
        ('arabian', 'Arabian'),
        ('thoroughbred', 'Thoroughbred'),
        ('quarterhorse', 'Quarter Horse'),
        # add more horse breeds here
    ]

    BREED_CHOICES = DOG_BREEDS + HORSE_BREEDS

    species = forms.ChoiceField(choices=SPECIES_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    breed = forms.ChoiceField(choices=BREED_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}))

    age = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}))

    gender = forms.ChoiceField(
        choices=[
            ('M', 'Male'),
            ('F', 'Female'),
            ('O', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    owner_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    owner_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-input'}))
    weight = forms.DecimalField(max_digits=5, decimal_places=2, required=False,
                                widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}))
    medical_history = forms.CharField(required=False,
                                      widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}))

    class Meta:
        model = Animal
        fields = [
            'name', 'species', 'breed', 'age', 'date_of_birth', 'owner_name',
            'gender', 'owner_phone', 'owner_email', 'weight', 'medical_history',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-input'}),
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
