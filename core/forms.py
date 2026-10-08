from django import forms
from django.utils import timezone
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
            'date_of_birth', 'owner_name', 'photo', 'assigned_users', 'assigned_vet',
            'status', 'status_since', 'status_notes', 'specialisation',
            'sex', 'is_neutered', 'colour_markings', 'microchip_number', 'brand_or_tattoo',
            'acquisition_date', 'acquisition_source', 'acquired_from',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'age': forms.NumberInput(attrs={'step': '0.01'}),
            'assigned_users': forms.CheckboxSelectMultiple(),
            'status_since': forms.DateInput(attrs={'type': 'date'}),
            'acquisition_date': forms.DateInput(attrs={'type': 'date'}),
            'status_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reason for current status (optional)'}),
            'colour_markings': forms.TextInput(attrs={'placeholder': 'e.g. Black & tan, white chest blaze'}),
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

    def clean_microchip_number(self):
        # Blank must be stored as NULL so the unique constraint allows many unchipped animals.
        return (self.cleaned_data.get('microchip_number') or '').strip() or None


class AnimalStatusForm(forms.ModelForm):
    """Quick duty-status change from the animal profile."""
    class Meta:
        model = Animal
        fields = ['status', 'status_since', 'status_notes']
        widgets = {
            'status_since': forms.DateInput(attrs={'type': 'date'}),
            'status_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reason / notes'}),
        }


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


# ------------------------------
# Deployments
# ------------------------------
from .models import Deployment, DeploymentTeam, DeploymentFind, Branch  # noqa: E402

DATETIME_LOCAL = forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')


def _branch_animals(branch, include=None):
    """Animals that can be deployed: active strength of the branch, plus any already on the record."""
    qs = Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES)
    if branch is not None:
        qs = qs.filter(branch=branch)
    if include:
        qs = qs | Animal.objects.filter(pk__in=include)
    return qs.distinct().order_by('name')


class DeploymentForm(forms.ModelForm):
    class Meta:
        model = Deployment
        fields = [
            'branch', 'deployment_type', 'started_at', 'ended_at', 'location', 'ob_number', 'requested_by',
            'status', 'outcome', 'arrests', 'persons_located', 'summary',
        ]
        widgets = {
            'started_at': DATETIME_LOCAL,
            'ended_at': DATETIME_LOCAL,
            'summary': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What happened, actions taken, notable behaviour…'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Moshi bus terminal, Bay 3'}),
            'ob_number': forms.TextInput(attrs={'placeholder': 'e.g. MOS/RB/1234/2026'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('started_at', 'ended_at'):
            self.fields[name].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['outcome'].required = False
        if user is not None and user.role != 'superadmin':
            # Branch staff always log against their own branch.
            del self.fields['branch']
        else:
            self.fields['branch'].queryset = Branch.objects.filter(is_active=True).order_by('name')

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('started_at'), cleaned.get('ended_at')
        if start and end and end < start:
            self.add_error('ended_at', 'End time cannot be before the start time.')
        if cleaned.get('status') == 'completed':
            if not cleaned.get('outcome'):
                self.add_error('outcome', 'Record the outcome for a completed deployment.')
            if not end:
                self.add_error('ended_at', 'Record when a completed deployment ended.')
        return cleaned


from .health import animal_overdue  # noqa: E402


def _deployable_label(animal):
    """Option text that warns when an animal isn't fit or isn't certified for its role."""
    warnings = [] if animal.is_fit_for_duty else [animal.get_status_display()]
    if animal.required_cert_type:
        cert = animal.role_certificate
        if cert is None:
            warnings.append('not certified')
        elif cert.state == 'expired':
            warnings.append('certificate expired')
    if animal_overdue(animal):
        warnings.append('treatment overdue')
    suffix = f" ⚠ {', '.join(warnings)}" if warnings else ''
    return f"{animal.name} · {animal.force_number} ({animal.get_species_display()}){suffix}"


class DeploymentTeamForm(forms.ModelForm):
    class Meta:
        model = DeploymentTeam
        fields = ['animal', 'handler', 'performance', 'notes']
        widgets = {'notes': forms.TextInput(attrs={'placeholder': 'Behaviour, indications…'})}

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        current = [self.instance.animal_id] if self.instance.pk else None
        self.fields['animal'].queryset = _branch_animals(branch, current)
        self.fields['animal'].label_from_instance = _deployable_label
        handlers = CustomUser.objects.filter(is_active=True)
        if branch is not None:
            handlers = handlers.filter(branch=branch)
        self.fields['handler'].queryset = handlers.order_by('first_name', 'username')
        self.fields['handler'].label_from_instance = lambda u: u.get_full_name() or u.username


class DeploymentFindForm(forms.ModelForm):
    class Meta:
        model = DeploymentFind
        fields = ['find_type', 'description', 'quantity', 'unit', 'indicated_by']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'e.g. Cannabis in luggage'}),
            'quantity': forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
        }

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        current = [self.instance.indicated_by_id] if self.instance.pk and self.instance.indicated_by_id else None
        self.fields['indicated_by'].queryset = _branch_animals(branch, current)


class _RequireTeam(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        animals = [f.cleaned_data['animal'] for f in self.forms
                   if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('animal')]
        if not animals:
            raise ValidationError('Add at least one animal to the deployment team.')
        if len(animals) != len(set(animals)):
            raise ValidationError('The same animal is listed twice.')


DeploymentTeamFormSet = inlineformset_factory(
    Deployment, DeploymentTeam, form=DeploymentTeamForm, formset=_RequireTeam, extra=0, can_delete=True,
)
DeploymentFindFormSet = inlineformset_factory(
    Deployment, DeploymentFind, form=DeploymentFindForm, extra=0, can_delete=True,
)


# ------------------------------
# Handler teams & certifications
# ------------------------------
from .models import Certification, HandlerAssignment  # noqa: E402


def _handler_label(user):
    return f"{user.get_full_name() or user.username} ({user.get_role_display()})"


class HandlerAssignmentForm(forms.ModelForm):
    class Meta:
        model = HandlerAssignment
        fields = ['handler', 'role', 'start_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.TextInput(attrs={'placeholder': 'e.g. Handover after course completion'}),
        }

    def __init__(self, *args, animal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.animal = animal
        users = CustomUser.objects.filter(is_active=True)
        if animal is not None:
            users = users.filter(branch=animal.branch)
        self.fields['handler'].queryset = users.order_by('role', 'first_name', 'username')
        self.fields['handler'].label_from_instance = _handler_label

    def clean(self):
        cleaned = super().clean()
        handler, role = cleaned.get('handler'), cleaned.get('role')
        if self.animal is not None and handler:
            current = self.animal.handler_assignments.filter(handler=handler, end_date__isnull=True)
            # Promoting a secondary handler to primary is allowed; anything else is a duplicate.
            if current.exists() and not (role == 'primary' and not current.filter(role='primary').exists()):
                self.add_error('handler', 'This handler is already on the team.')
        return cleaned


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['cert_type', 'handler', 'certificate_number', 'issued_by', 'issued_date', 'expiry_date',
                  'document', 'notes']
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'issued_by': forms.TextInput(attrs={'placeholder': 'e.g. TPF K9 Training School, Moshi'}),
            'notes': forms.TextInput(attrs={'placeholder': 'Score, assessor, conditions…'}),
        }

    def __init__(self, *args, animal=None, **kwargs):
        super().__init__(*args, **kwargs)
        users = CustomUser.objects.filter(is_active=True)
        if animal is not None:
            users = users.filter(branch=animal.branch)
            if not self.is_bound and not self.instance.pk:
                self.initial.setdefault('cert_type', animal.required_cert_type)
                primary = animal.primary_handler
                if primary:
                    self.initial.setdefault('handler', primary.pk)
        self.fields['handler'].queryset = users.order_by('first_name', 'username')
        self.fields['handler'].label_from_instance = _handler_label

    def clean(self):
        cleaned = super().clean()
        issued, expiry = cleaned.get('issued_date'), cleaned.get('expiry_date')
        if issued and expiry and expiry <= issued:
            self.add_error('expiry_date', 'Expiry must be after the issue date.')
        return cleaned


# ------------------------------
# Horse care: farrier, tack, housing
# ------------------------------
from .models import HoofCareRecord, HousingAssignment, HousingUnit, TackItem  # noqa: E402

DATE_INPUT = forms.DateInput(attrs={'type': 'date'})


def _branch_horses(branch):
    qs = Animal.objects.filter(species='horse', status__in=Animal.ACTIVE_STATUSES)
    return (qs.filter(branch=branch) if branch is not None else qs).order_by('name')


class HoofCareForm(forms.ModelForm):
    class Meta:
        model = HoofCareRecord
        fields = ['animal', 'date', 'service', 'hooves', 'farrier', 'condition', 'next_due', 'notes']
        widgets = {
            'date': DATE_INPUT, 'next_due': DATE_INPUT,
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Findings, nail size, pads, follow-up...'}),
            'farrier': forms.TextInput(attrs={'placeholder': 'e.g. J. Mushi (contract farrier)'}),
        }
        labels = {'animal': 'Horse'}

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['animal'].queryset = _branch_horses(branch)
        self.fields['next_due'].help_text = (
            f'Leave blank to schedule {HoofCareRecord.DEFAULT_INTERVAL_DAYS // 7} weeks after this visit.')
        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault('date', timezone.localdate())

    def clean(self):
        cleaned = super().clean()
        date, next_due = cleaned.get('date'), cleaned.get('next_due')
        if date and date > timezone.localdate():
            self.add_error('date', 'A farrier visit cannot be recorded in the future.')
        if date and next_due and next_due <= date:
            self.add_error('next_due', 'Next visit must be after this visit.')
        return cleaned


class TackItemForm(forms.ModelForm):
    class Meta:
        model = TackItem
        fields = ['branch', 'item_type', 'asset_tag', 'description', 'size', 'assigned_horse', 'condition',
                  'last_inspected', 'notes', 'is_active']
        widgets = {'last_inspected': DATE_INPUT, 'notes': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        branch = self.instance.branch if self.instance.pk else getattr(user, 'branch', None)
        if user is not None and user.role != 'superadmin':
            del self.fields['branch']
        else:
            self.fields['branch'].queryset = Branch.objects.filter(is_active=True).order_by('name')
            branch = None
        horses = _branch_horses(branch)
        if self.instance.pk and self.instance.assigned_horse_id:
            horses = horses | Animal.objects.filter(pk=self.instance.assigned_horse_id)
        self.fields['assigned_horse'].queryset = horses.distinct()
        self.fields['assigned_horse'].required = False

    def clean(self):
        cleaned = super().clean()
        horse = cleaned.get('assigned_horse')
        branch = cleaned.get('branch') or (self.instance.branch if self.instance.branch_id else None)
        if horse and branch and horse.branch_id != branch.id:
            self.add_error('assigned_horse', f'{horse.name} is not in {branch.name}.')
        if cleaned.get('last_inspected') and cleaned['last_inspected'] > timezone.localdate():
            self.add_error('last_inspected', 'Inspection date cannot be in the future.')
        return cleaned


class HousingUnitForm(forms.ModelForm):
    class Meta:
        model = HousingUnit
        fields = ['name', 'kind', 'capacity', 'notes', 'is_active']
        widgets = {'name': forms.TextInput(attrs={'placeholder': 'e.g. Stable Block A, Stall 3'})}

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.branch = branch if branch is not None else getattr(self.instance, 'branch', None)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        clash = HousingUnit.objects.filter(branch=self.branch, name__iexact=name).exclude(pk=self.instance.pk)
        if self.branch is not None and clash.exists():
            raise ValidationError('A unit with this name already exists in the branch.')
        return name

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if capacity < 1:
            raise ValidationError('Capacity must be at least 1.')
        return capacity


# Which animals each kind of unit is suitable for (None = any species).
UNIT_SPECIES = {'stall': 'horse', 'paddock': 'horse', 'kennel': 'dog', 'isolation': None, 'other': None}


class HousingMoveForm(forms.ModelForm):
    class Meta:
        model = HousingAssignment
        fields = ['animal', 'unit', 'start_date', 'notes']
        widgets = {'start_date': DATE_INPUT, 'notes': forms.TextInput(attrs={'placeholder': 'Reason for move (optional)'})}
        labels = {'unit': 'Move to', 'start_date': 'From'}

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        animals = Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES)
        units = HousingUnit.objects.filter(is_active=True)
        if branch is not None:
            animals, units = animals.filter(branch=branch), units.filter(branch=branch)
        self.fields['animal'].queryset = animals.order_by('species', 'name')
        self.fields['animal'].label_from_instance = lambda a: f"{a.name} ({a.get_species_display()})"
        self.fields['unit'].queryset = units.order_by('kind', 'name')
        self.fields['unit'].label_from_instance = lambda u: f"{u.name} ({u.get_kind_display()})"
        if not self.is_bound:
            self.initial.setdefault('start_date', timezone.localdate())

    def clean(self):
        cleaned = super().clean()
        animal, unit = cleaned.get('animal'), cleaned.get('unit')
        if not animal or not unit:
            return cleaned
        if animal.branch_id != unit.branch_id:
            self.add_error('unit', 'Unit belongs to another branch.')
        wanted = UNIT_SPECIES.get(unit.kind)
        if wanted and animal.species != wanted:
            self.add_error('unit', f'A {unit.get_kind_display().lower()} is not suitable for a {animal.get_species_display().lower()}.')
        current = animal.housing_assignments.filter(end_date__isnull=True).first()
        if current and current.unit_id == unit.id:
            self.add_error('unit', f'{animal.name} is already in {unit.name}.')
        occupied = unit.assignments.filter(end_date__isnull=True).exclude(animal=animal).count()
        if occupied >= unit.capacity:
            self.add_error('unit', f'{unit.name} is full ({occupied}/{unit.capacity}).')
        return cleaned


# ------------------------------
# Stores
# ------------------------------
from decimal import Decimal  # noqa: E402
from .models import StockItem, StockMovement  # noqa: E402


class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ['branch', 'name', 'category', 'unit', 'reorder_level', 'reorder_quantity', 'supplier', 'notes', 'is_active']
        widgets = {
            'reorder_level': forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
            'reorder_quantity': forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and user.role != 'superadmin':
            del self.fields['branch']
        else:
            self.fields['branch'].queryset = Branch.objects.filter(is_active=True).order_by('name')

    def clean(self):
        cleaned = super().clean()
        branch = cleaned.get('branch') or (self.instance.branch if self.instance.branch_id else None)
        name = (cleaned.get('name') or '').strip()
        if branch and name and StockItem.objects.filter(branch=branch, name__iexact=name).exclude(pk=self.instance.pk).exists():
            self.add_error('name', 'This branch already has an item with this name.')
        for f in ('reorder_level', 'reorder_quantity'):
            if cleaned.get(f) is not None and cleaned[f] < 0:
                self.add_error(f, 'Cannot be negative.')
        return cleaned


class StockMovementForm(forms.ModelForm):
    """Receive / issue / write off. Quantity is entered positive; the view applies the sign."""
    KIND_CHOICES = [('received', 'Receive delivery'), ('issued', 'Issue / use'), ('wasted', 'Write off (expired, damaged)')]

    kind = forms.ChoiceField(choices=KIND_CHOICES)

    class Meta:
        model = StockMovement
        fields = ['kind', 'quantity', 'date', 'animal', 'batch_number', 'expiry_date', 'reference', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
        }
        labels = {'animal': 'For animal (optional)'}

    def __init__(self, *args, item=None, allowed_kinds=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = item
        if allowed_kinds is not None:
            self.fields['kind'].choices = [c for c in self.KIND_CHOICES if c[0] in allowed_kinds]
        animals = Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES)
        if item is not None:
            animals = animals.filter(branch=item.branch)
        self.fields['animal'].queryset = animals.order_by('name')
        self.fields['animal'].required = False
        if not self.is_bound:
            self.initial.setdefault('date', timezone.localdate())

    def clean(self):
        cleaned = super().clean()
        kind, qty, day = cleaned.get('kind'), cleaned.get('quantity'), cleaned.get('date')
        if qty is not None and qty <= 0:
            self.add_error('quantity', 'Enter a quantity greater than zero.')
        if day and day > timezone.localdate():
            self.add_error('date', 'Cannot record a movement in the future.')
        if kind != 'received':
            cleaned['expiry_date'] = None
            cleaned['batch_number'] = cleaned.get('batch_number') or ''
        if kind in StockMovement.OUTGOING and qty and self.item is not None and qty > self.item.on_hand:
            self.add_error('quantity', f'Only {self.item.on_hand:g} {self.item.get_unit_display()} in stock.')
        return cleaned


class StockTakeForm(forms.Form):
    counted = forms.DecimalField(label='Counted on shelf', min_value=Decimal('0'), max_digits=12, decimal_places=2,
                                 widget=forms.NumberInput(attrs={'step': 'any', 'min': '0'}))
    notes = forms.CharField(required=False, max_length=255,
                            widget=forms.TextInput(attrs={'placeholder': 'Reason for any difference'}))
