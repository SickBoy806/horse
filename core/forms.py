from django import forms
from .models import TrainingRecord
from .models import Report
from django.forms import inlineformset_factory
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


class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = [
            'training_tracking', 'training_sniffer', 'training_explosives',
            'training_govt_trophies', 'training_narcotics', 'training_other',
            'training_place', 'training_duration', 'training_time', 'training_handler'
        ]
        widgets = {
            'training_other': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Describe any other training types or special notes...'
            }),
            'training_place': forms.TextInput(attrs={
                'placeholder': 'Training facility or location'
            }),
            'training_duration': forms.TextInput(attrs={
                'placeholder': 'e.g., 2 weeks, 40 hours'
            }),
            'training_time': forms.TextInput(attrs={
                'placeholder': 'e.g., 9:00 AM - 5:00 PM'
            }),
            'training_handler': forms.TextInput(attrs={
                'placeholder': 'Handler name'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Check if at least one training type is selected
        training_types = [
            cleaned_data.get('training_tracking'),
            cleaned_data.get('training_sniffer'),
            cleaned_data.get('training_explosives'),
            cleaned_data.get('training_govt_trophies'),
            cleaned_data.get('training_narcotics'),
        ]

        has_other_training = cleaned_data.get('training_other', '').strip()

        if not any(training_types) and not has_other_training:
            raise forms.ValidationError(
                "Please select at least one training type or specify other training."
            )

        return cleaned_data


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'report_type', 'specific_report_type', 'description', 'file']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.role_category_value = None  # default

        if user:
            role = getattr(user, 'role', None)

            if role in ['trainer', 'worker']:
                self.fields['specific_report_type'].choices = [
                    choice for choice in Report.SPECIFIC_REPORT_TYPES
                    if choice[0] in [
                        'training_progress', 'training_log', 'performance_eval',
                        'behavior_assessment', 'missed_training', 'training_schedule',
                        'special_skills', 'daily_care', 'inventory', 'facility_maintenance',
                        'animal_condition', 'work_shift', 'incident'
                    ]
                ]
                self.role_category_value = 'user'

            elif role == 'veterinarian':
                self.fields['specific_report_type'].choices = [
                    choice for choice in Report.SPECIFIC_REPORT_TYPES
                    if choice[0] in [
                        'medical_record', 'vet_activity_log', 'treatment_medication',
                        'vaccination_schedule', 'lab_results', 'injury_illness',
                        'disease_tracking'
                    ]
                ]
                self.role_category_value = 'veterinarian'

            elif role == 'admin':
                self.fields['specific_report_type'].choices = [
                    choice for choice in Report.SPECIFIC_REPORT_TYPES
                    if choice[0] in [
                        'staff_attendance', 'animal_assignment', 'facility_resource',
                        'task_completion', 'support_requests', 'animal_acquisition'
                    ]
                ]
                self.role_category_value = 'admin'

            elif role == 'superadmin':
                self.fields['specific_report_type'].choices = [
                    choice for choice in Report.SPECIFIC_REPORT_TYPES
                    if choice[0] in [
                        'operations_summary', 'cross_branch_performance', 'financial_resource',
                        'incident_safety', 'compliance_audit', 'staff_productivity',
                        'long_term_performance'
                    ]
                ]
                self.role_category_value = 'superadmin'

            else:
                self.fields['specific_report_type'].choices = []
                self.role_category_value = None
