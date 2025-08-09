from django import forms
from django.core.exceptions import ValidationError
from .models import (
    VetTask, SupportTicket, TicketReply, Animal, Message, 
    MedicalRecord, AnimalLog, EquipmentLog, EmergencyIncident,
    DailyActivityReport
)
from accounts.models import CustomUser


class VetTaskForm(forms.ModelForm):
    class Meta:
        model = VetTask
        fields = ['title', 'description', 'animal', 'assigned_to', 'priority', 'due_date', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show users and animals from the same branch
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                branch=user.branch,
                role__in=['veterinarian', 'user', 'staff']
            )
            self.fields['animal'].queryset = Animal.objects.filter(branch=user.branch)


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = [
            'name', 'species', 'breed', 'force_number', 'age', 
            'date_of_birth', 'owner_name', 'photo', 'assigned_users', 'assigned_vet'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'age': forms.NumberInput(attrs={'step': '0.01'}),
            'assigned_users': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show users from the same branch for assignment
            branch_users = CustomUser.objects.filter(branch=user.branch)
            self.fields['assigned_users'].queryset = branch_users
            self.fields['assigned_vet'].queryset = branch_users.filter(role='veterinarian')

    def clean_force_number(self):
        force_number = self.cleaned_data.get('force_number')
        if force_number:
            # Check if force number already exists (excluding current instance)
            existing = Animal.objects.filter(force_number=force_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("An animal with this force number already exists.")
        return force_number


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'animal', 'report_type', 'diagnosis', 'treatment', 'document',
            'weight', 'temperature', 'mating_date', 'expected_delivery_date',
            'breeding_method', 'lab_test_name', 'test_result', 'sample_type',
            'dewormer_name', 'next_deworming_date', 'cause_of_death',
            'postmortem_findings', 'transfer_from', 'transfer_to',
            'reason_for_transfer', 'referred_to', 'referral_reason',
            'dip_type', 'dipping_location', 'surgery_type', 'anesthesia_used',
            'vaccine_name', 'next_due_date'
        ]
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 4}),
            'treatment': forms.Textarea(attrs={'rows': 4}),
            'mating_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'next_deworming_date': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
            'weight': forms.NumberInput(attrs={'step': '0.01'}),
            'temperature': forms.NumberInput(attrs={'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show animals from the same branch
            self.fields['animal'].queryset = Animal.objects.filter(branch=user.branch)


class AnimalLogForm(forms.ModelForm):
    class Meta:
        model = AnimalLog
        fields = ['animal', 'activity_type', 'notes', 'photo']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show animals from the same branch
            self.fields['animal'].queryset = Animal.objects.filter(branch=user.branch)


class EquipmentLogForm(forms.ModelForm):
    class Meta:
        model = EquipmentLog
        fields = ['equipment', 'action', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class EmergencyIncidentForm(forms.ModelForm):
    class Meta:
        model = EmergencyIncident
        fields = ['animal', 'incident_type', 'severity', 'description', 'photo', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show animals from the same branch
            self.fields['animal'].queryset = Animal.objects.filter(branch=user.branch)


class DailyActivityReportForm(forms.ModelForm):
    class Meta:
        model = DailyActivityReport
        fields = ['date', 'summary', 'issues_faced', 'hours_worked', 'animals_cared_for']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'summary': forms.Textarea(attrs={'rows': 4}),
            'issues_faced': forms.Textarea(attrs={'rows': 3}),
            'hours_worked': forms.NumberInput(attrs={'step': '0.25'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show animals from the same branch
            self.fields['animals_cared_for'].queryset = Animal.objects.filter(branch=user.branch)


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Write your message...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.branch:
            # Only show users from the same branch (excluding sender)
            self.fields['receiver'].queryset = CustomUser.objects.filter(
                branch=user.branch
            ).exclude(id=user.id)


class MessageReplyForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Type your reply...'}),
        }
