import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Animal(models.Model):
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('horse', 'Horse'),
    ]

    STATUS_OPERATIONAL = 'operational'
    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('in_training', 'In Training'),
        ('sick', 'Sick / Injured'),
        ('retired', 'Retired'),
        ('deceased', 'Deceased'),
        ('transferred', 'Transferred Out'),
    ]
    # Statuses that still count towards a branch's active strength.
    ACTIVE_STATUSES = ('operational', 'in_training', 'sick')

    SPECIALISATION_CHOICES = [
        ('general', 'General Purpose'),
        ('explosives', 'Explosives Detection'),
        ('narcotics', 'Narcotics Detection'),
        ('tracking', 'Tracking'),
        ('search_rescue', 'Search & Rescue'),
        ('patrol', 'Patrol'),
        ('wildlife', 'Wildlife / Trophy Detection'),
        ('crowd_control', 'Crowd Control'),
        ('ceremonial', 'Ceremonial'),
        ('breeding', 'Breeding'),
    ]

    SEX_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    ACQUISITION_CHOICES = [
        ('bred', 'Bred In-house'),
        ('purchased', 'Purchased'),
        ('donated', 'Donated'),
        ('transferred', 'Transferred In'),
        ('seized', 'Seized / Confiscated'),
    ]

    name = models.CharField(max_length=255)
    species = models.CharField(max_length=100, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True, null=True)
    force_number = models.CharField(max_length=100, unique=True)
    age = models.DecimalField(max_digits=5, decimal_places=2)
    date_of_birth = models.DateField(null=True, blank=True)
    owner_name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='animal_photos/', blank=True, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    assigned_users = models.ManyToManyField(CustomUser, related_name='assigned_animals', blank=True)
    assigned_vet = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='vet_animals')

    # Duty status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPERATIONAL, db_index=True)
    status_since = models.DateField(null=True, blank=True)
    status_notes = models.TextField(blank=True)
    specialisation = models.CharField(max_length=20, choices=SPECIALISATION_CHOICES, default='general')

    # Identification
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, blank=True)
    is_neutered = models.BooleanField(default=False)
    colour_markings = models.CharField('Colour & markings', max_length=255, blank=True)
    microchip_number = models.CharField(max_length=64, unique=True, null=True, blank=True)
    brand_or_tattoo = models.CharField('Brand / tattoo mark', max_length=64, blank=True)

    # Acquisition
    acquisition_date = models.DateField(null=True, blank=True)
    acquisition_source = models.CharField(max_length=20, choices=ACQUISITION_CHOICES, blank=True)
    acquired_from = models.CharField('Acquired from', max_length=255, blank=True,
                                     help_text='Breeder, supplier, donor or originating branch.')

    # Pedigree
    sire = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sired',
                             limit_choices_to={'sex': 'male'})
    dam = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='mothered',
                            limit_choices_to={'sex': 'female'})
    litter = models.ForeignKey('Litter', on_delete=models.SET_NULL, null=True, blank=True, related_name='offspring')

    # Printed in the ID-card QR code; regenerate to invalidate a lost card.
    card_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    card_issued = models.DateField(null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.force_number})"

    @property
    def is_fit_for_duty(self):
        return self.status == self.STATUS_OPERATIONAL

    @property
    def current_handlers(self):
        return self.handler_assignments.filter(end_date__isnull=True).select_related('handler')

    @property
    def primary_handler(self):
        assignment = self.handler_assignments.filter(end_date__isnull=True, role='primary').select_related('handler').first()
        return assignment.handler if assignment else None

    @property
    def current_housing(self):
        assignment = self.housing_assignments.filter(end_date__isnull=True).select_related('unit').first()
        return assignment.unit if assignment else None

    @property
    def required_cert_type(self):
        return Certification.REQUIRED_FOR_SPECIALISATION.get(self.specialisation)

    @property
    def role_certificate(self):
        """Most recent certificate for the animal's specialisation (None if never certified)."""
        cert_type = self.required_cert_type
        if not cert_type:
            return None
        return self.certifications.filter(cert_type=cert_type).order_by('-expiry_date', '-id').first()

    @property
    def status_badge(self):
        """tpf-badge colour modifier for this status."""
        return {
            'operational': 'tpf-badge-green',
            'in_training': 'tpf-badge-blue',
            'sick': 'tpf-badge-amber',
            'retired': 'tpf-badge-purple',
            'deceased': '',
            'transferred': '',
        }.get(self.status, '')

    class Meta:
        ordering = ['-created_at']


class AnimalStatusChange(models.Model):
    """Audit trail of duty-status changes."""
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Animal.STATUS_CHOICES, blank=True)
    new_status = models.CharField(max_length=20, choices=Animal.STATUS_CHOICES)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.animal.name}: {self.old_status or '—'} → {self.new_status}"


class VetTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='vet_tasks')
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assigned_vet_tasks')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_vet_tasks')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_assigned = models.DateTimeField(auto_now_add=True)  # or just DateTimeField()

    def __str__(self):
        return f"{self.title} - {self.animal.name}"

    class Meta:
        ordering = ['-created_at']


class MedicalRecord(models.Model):
    REPORT_TYPES = [
        ('breeding', 'Breeding'),
        ('lab_diagnosis', 'Lab Diagnosis'),
        ('deworming', 'Deworming'),
        ('postmortem', 'Postmortem'),
        ('transfer', 'Transfer'),
        ('referral', 'Referral'),
        ('dipping', 'Dipping'),
        ('surgery', 'Surgery'),
        ('vaccination', 'Vaccination'),
        ('checkup', 'Routine Checkup'),
        ('emergency', 'Emergency'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='medical_records')
    veterinarian = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='medical_records')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    diagnosis = models.TextField()
    treatment = models.TextField()
    document = models.FileField(upload_to='medical_documents/', blank=True, null=True)
    
    # General fields
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    
    # Breeding specific
    mating_date = models.DateField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    breeding_method = models.CharField(max_length=100, blank=True, null=True)
    
    # Lab diagnosis specific
    lab_test_name = models.CharField(max_length=255, blank=True, null=True)
    test_result = models.TextField(blank=True, null=True)
    sample_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Deworming specific
    dewormer_name = models.CharField(max_length=100, blank=True, null=True)
    next_deworming_date = models.DateField(blank=True, null=True)
    
    # Postmortem specific
    cause_of_death = models.TextField(blank=True, null=True)
    postmortem_findings = models.TextField(blank=True, null=True)
    
    # Transfer specific
    transfer_from = models.CharField(max_length=255, blank=True, null=True)
    transfer_to = models.CharField(max_length=255, blank=True, null=True)
    reason_for_transfer = models.TextField(blank=True, null=True)
    
    # Referral specific
    referred_to = models.CharField(max_length=255, blank=True, null=True)
    referral_reason = models.TextField(blank=True, null=True)
    
    # Dipping specific
    dip_type = models.CharField(max_length=100, blank=True, null=True)
    dipping_location = models.CharField(max_length=255, blank=True, null=True)
    
    # Surgery specific
    surgery_type = models.CharField(max_length=255, blank=True, null=True)
    anesthesia_used = models.CharField(max_length=255, blank=True, null=True)
    
    # Vaccination specific
    vaccine_name = models.CharField(max_length=255, blank=True, null=True)
    next_due_date = models.DateField(blank=True, null=True)
    
    date_recorded = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.report_type.title()} - {self.animal.name} ({self.date_recorded.date()})"

    class Meta:
        ordering = ['-date_recorded']


class AnimalLog(models.Model):
    ACTIVITY_TYPES = [
        ('feeding', 'Feeding'),
        ('cleaning', 'Cleaning'),
        ('exercise', 'Exercise'),
        ('health_observation', 'Health Observation'),
        ('incident', 'Incident'),
        ('training', 'Training'),
        ('grooming', 'Grooming'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='animal_logs')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    notes = models.TextField()
    photo = models.ImageField(upload_to='activity_photos/', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.animal.name} - {self.get_activity_type_display()} by {self.user.username}"

    class Meta:
        ordering = ['-date']


class EquipmentLog(models.Model):
    EQUIPMENT_CHOICES = [
        ('leash', 'Leash'),
        ('feeding_kit', 'Feeding Kit'),
        ('first_aid', 'First Aid Kit'),
        ('cleaning_tools', 'Cleaning Tools'),
        ('training_gear', 'Training Gear'),
        ('medical_equipment', 'Medical Equipment'),
        ('grooming_tools', 'Grooming Tools'),
        ('other', 'Other'),
    ]
    
    ACTION_CHOICES = [
        ('check_out', 'Checked Out'),
        ('check_in', 'Returned'),
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='equipment_logs')
    equipment = models.CharField(max_length=100, choices=EQUIPMENT_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_equipment_display()} - {self.get_action_display()}"

    class Meta:
        ordering = ['-timestamp']


class EmergencyIncident(models.Model):
    INCIDENT_TYPES = [
        ('injury', 'Injury'),
        ('escape', 'Escape'),
        ('illness', 'Illness'),
        ('aggression', 'Aggression'),
        ('equipment_failure', 'Equipment Failure'),
        ('fire', 'Fire'),
        ('theft', 'Theft'),
        ('other', 'Other'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reported_incidents')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='incidents', null=True, blank=True)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField()
    photo = models.ImageField(upload_to='emergency_photos/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_incidents')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.animal.name if self.animal else 'General'} ({self.date_reported.date()})"

    class Meta:
        ordering = ['-date_reported']


class DailyActivityReport(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='daily_reports')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    date = models.DateField()
    summary = models.TextField()
    issues_faced = models.TextField(blank=True, null=True)
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2)
    animals_cared_for = models.ManyToManyField(Animal, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user.username} on {self.date}"

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('emergency_reported', 'Emergency Reported'),
        ('medical_record_added', 'Medical Record Added'),
        ('animal_assigned', 'Animal Assigned'),
        ('message_received', 'Message Received'),
        ('system_alert', 'System Alert'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True, blank=True)  # NEW

    class Meta:
        ordering = ['-timestamp']



class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    subject = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.subject}"

    class Meta:
        ordering = ['-created_at']


class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    replied_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.replied_by} on ticket #{self.ticket.id}"

    class Meta:
        ordering = ['created_at']


class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('assign', 'Assign Task'),
        ('approve', 'Approve Report'),
        ('complete_task', 'Complete Task'),
        ('emergency_report', 'Emergency Report'),
        ('error', 'Error'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='system_logs')
    role = models.CharField(max_length=50)
    branch = models.CharField(max_length=100)  # OLD field, keep temporarily
    branch_fk = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)  # NEW FK field
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-timestamp']


class Report(models.Model):
    ROLE_CATEGORIES = [
        ('user', 'User (Trainer / Worker)'),
        ('veterinarian', 'Veterinarian'),
        ('admin', 'Admin'),
        ('superadmin', 'Super Admin'),
    ]

    SPECIFIC_REPORT_TYPES = [
        # User (Trainer / Worker)
        ('training_progress', 'Training Progress Report'),
        ('training_log', 'Daily/Weekly Training Log'),
        ('performance_eval', 'Performance Evaluation'),
        ('behavior_assessment', 'Behavioral Assessment Report'),
        ('missed_training', 'Missed / Incomplete Training Sessions'),
        ('training_schedule', 'Training Schedule Report'),
        ('special_skills', 'Specialized Skill Tracking'),
        ('daily_care', 'Daily Care Log'),
        ('inventory', 'Inventory & Supplies Report'),
        ('facility_maintenance', 'Facility Maintenance Report'),
        ('animal_condition', 'Animal Condition Check'),
        ('work_shift', 'Work Shift Log'),
        ('incident', 'Incident Report'),

        # Veterinarian
        ('medical_record', 'Medical Record Report'),
        ('vet_activity_log', 'Daily Veterinary Activity Log'),
        ('treatment_medication', 'Treatment & Medication Report'),
        ('vaccination_schedule', 'Vaccination Schedule & Compliance Report'),
        ('lab_results', 'Lab Test Results Report'),
        ('injury_illness', 'Injury/Illness Incident Report'),
        ('disease_tracking', 'Disease Outbreak Tracking Report'),

        # Admin
        ('staff_attendance', 'Staff Attendance Report'),
        ('animal_assignment', 'Animal Assignment Report'),
        ('facility_resource', 'Facility Resource Report'),
        ('task_completion', 'Task Completion Status'),
        ('support_requests', 'Support Requests Report'),
        ('animal_acquisition', 'Animal Acquisition & Retirement Report'),

        # Super Admin
        ('operations_summary', 'Overall Operations Summary'),
        ('cross_branch_performance', 'Cross-Branch Performance Report'),
        ('financial_resource', 'Financial & Resource Usage Report'),
        ('incident_safety', 'Incident & Safety Reports'),
        ('compliance_audit', 'Compliance & Audit Report'),
        ('staff_productivity', 'Staff Productivity Report'),
        ('long_term_performance', 'Long-Term Animal Performance & Health Trends'),
    ]

    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('incident', 'Incident Report'),
        ('medical', 'Medical Report'),
        ('custom', 'Custom Report'),
    ]

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    role_category = models.CharField(max_length=20, choices=ROLE_CATEGORIES)
    specific_report_type = models.CharField(max_length=50, choices=SPECIFIC_REPORT_TYPES)

    description = models.TextField()
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='created_reports')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='reports')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_specific_report_type_display()} - {self.title}"

    class Meta:
        ordering = ['-date_created']



class TrainingRecord(models.Model):
    animal = models.ForeignKey(
        Animal, on_delete=models.CASCADE, related_name='training_records'
    )

    # Training Types
    training_tracking = models.BooleanField("Tracking", default=False)
    training_sniffer = models.BooleanField("Sniffer", default=False)
    training_explosives = models.BooleanField("Explosives", default=False)
    training_govt_trophies = models.BooleanField("Government Trophies", default=False)
    training_narcotics = models.BooleanField("Narcotics", default=False)
    training_other = models.TextField("Other Training", blank=True, null=True, help_text="Describe any other training")

    # Training Details
    training_place = models.CharField("Training Place", max_length=255)
    training_duration = models.CharField("Duration", max_length=100, help_text="e.g., 2 weeks, 30 hours")
    training_time = models.CharField("Training Time", max_length=100, help_text="e.g., Morning, 9:00 AM - 5:00 PM")
    training_handler = models.CharField("Training Handler", max_length=100)

    date_recorded = models.DateField("Date Recorded", auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        training_types = []
        if self.training_tracking: training_types.append("Tracking")
        if self.training_sniffer: training_types.append("Sniffer")
        if self.training_explosives: training_types.append("Explosives")
        if self.training_govt_trophies: training_types.append("Govt Trophies")
        if self.training_narcotics: training_types.append("Narcotics")

        types_str = ", ".join(training_types) if training_types else "General Training"
        return f"{self.animal.name} - {types_str} ({self.date_recorded})"

    class Meta:
        ordering = ['-date_recorded']


class TrainingSession(models.Model):
    training_record = models.ForeignKey(
        'TrainingRecord',
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    date = models.DateField()
    description = models.TextField()
    trainer = models.CharField(max_length=100, blank=True, null=True)  # optional external trainer
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # links to your CustomUser
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_training_sessions'
    )
    duration = models.CharField(max_length=50, blank=True, null=True)  # e.g., '2 hours', '1 week'
    result = models.TextField(blank=True, null=True)  # performance notes, remarks

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session for {self.training_record.animal.name} on {self.date}"

# ------------------------------
# Operations: deployments & results
# ------------------------------

class Deployment(models.Model):
    TYPE_CHOICES = [
        ('narcotics_search', 'Narcotics Search'),
        ('explosives_sweep', 'Explosives Sweep'),
        ('tracking', 'Suspect Tracking'),
        ('search_rescue', 'Search & Rescue'),
        ('patrol', 'Patrol'),
        ('crowd_control', 'Crowd / Public Order'),
        ('screening', 'Border / Airport Screening'),
        ('wildlife', 'Wildlife / Trophy Detection'),
        ('vip_escort', 'VIP Protection / Escort'),
        ('ceremonial', 'Ceremonial / Parade'),
        ('demonstration', 'Public Demonstration'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    OUTCOME_CHOICES = [
        ('positive', 'Positive Result'),
        ('negative', 'Nothing Found'),
        ('inconclusive', 'Inconclusive'),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='deployments')
    deployment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', db_index=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, blank=True)

    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255)
    ob_number = models.CharField('OB / case number', max_length=64, blank=True)
    requested_by = models.CharField('Requested by', max_length=255, blank=True,
                                    help_text='Unit or officer that requested support, e.g. CID Moshi.')
    summary = models.TextField('Operation summary', blank=True)

    arrests = models.PositiveIntegerField(default=0)
    persons_located = models.PositiveIntegerField('Persons located', default=0)

    animals = models.ManyToManyField(Animal, through='DeploymentTeam', related_name='deployments')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='deployments_logged')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.reference} — {self.get_deployment_type_display()}"

    def save(self, *args, **kwargs):
        if not self.reference:
            year = (self.started_at or timezone.now()).year
            prefix = f"DEP-{year}-"
            last = (Deployment.objects.filter(reference__startswith=prefix)
                    .order_by('-reference').values_list('reference', flat=True).first())
            seq = int(last.rsplit('-', 1)[1]) + 1 if last else 1
            self.reference = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    @property
    def duration(self):
        if self.ended_at and self.started_at and self.ended_at > self.started_at:
            return self.ended_at - self.started_at
        return None

    @property
    def outcome_badge(self):
        return {'positive': 'tpf-badge-green', 'negative': '', 'inconclusive': 'tpf-badge-amber'}.get(self.outcome, '')

    @property
    def status_badge(self):
        return {'in_progress': 'tpf-badge-blue', 'completed': 'tpf-badge-green', 'cancelled': 'tpf-badge-red'}.get(self.status, '')


class DeploymentTeam(models.Model):
    """An animal (and its handler) on a deployment."""
    RATING_CHOICES = [(i, f'{i} / 5') for i in range(1, 6)]

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='team')
    animal = models.ForeignKey(Animal, on_delete=models.PROTECT, related_name='deployment_assignments')
    handler = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='handled_deployments')
    performance = models.PositiveSmallIntegerField('Performance rating', choices=RATING_CHOICES, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('deployment', 'animal')

    def __str__(self):
        return f"{self.animal.name} on {self.deployment.reference}"


class DeploymentFind(models.Model):
    FIND_CHOICES = [
        ('narcotics', 'Narcotics'),
        ('explosives', 'Explosives'),
        ('firearms', 'Firearms'),
        ('ammunition', 'Ammunition'),
        ('currency', 'Currency'),
        ('wildlife', 'Wildlife Trophy (ivory, horn, skins)'),
        ('person', 'Missing / Wanted Person'),
        ('evidence', 'Evidence / Property'),
        ('other', 'Other'),
    ]
    UNIT_CHOICES = [
        ('kg', 'kg'), ('g', 'g'), ('items', 'items'), ('rounds', 'rounds'),
        ('tzs', 'TZS'), ('usd', 'USD'), ('persons', 'persons'),
    ]

    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, related_name='finds')
    find_type = models.CharField(max_length=20, choices=FIND_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, blank=True)
    indicated_by = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='finds_indicated',
                                     help_text='Animal that made the indication.')

    def __str__(self):
        return f"{self.get_find_type_display()} ({self.deployment.reference})"


# ------------------------------
# Handler teams & certifications
# ------------------------------

class HandlerAssignment(models.Model):
    """A handler's period of responsibility for an animal. Open-ended (no end_date) means current."""
    ROLE_CHOICES = [('primary', 'Primary Handler'), ('secondary', 'Secondary Handler')]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='handler_assignments')
    handler = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='handler_assignments')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='primary')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='handler_assignments_made')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['end_date', 'role', '-start_date']
        constraints = [
            models.UniqueConstraint(fields=['animal'], condition=models.Q(end_date__isnull=True, role='primary'),
                                    name='one_current_primary_handler'),
        ]

    def __str__(self):
        return f"{self.handler} → {self.animal.name} ({self.get_role_display()})"

    @property
    def is_current(self):
        return self.end_date is None


class Certification(models.Model):
    TYPE_CHOICES = [
        ('explosives', 'Explosives Detection'),
        ('narcotics', 'Narcotics Detection'),
        ('tracking', 'Tracking'),
        ('search_rescue', 'Search & Rescue'),
        ('patrol', 'Patrol / Apprehension'),
        ('wildlife', 'Wildlife / Trophy Detection'),
        ('crowd_control', 'Crowd Control (Mounted)'),
        ('ceremonial', 'Ceremonial (Mounted)'),
        ('obedience', 'General Obedience'),
        ('fitness', 'Veterinary Fitness for Duty'),
    ]
    # Certification an animal needs for its specialisation to count as deployable.
    REQUIRED_FOR_SPECIALISATION = {
        'explosives': 'explosives', 'narcotics': 'narcotics', 'tracking': 'tracking',
        'search_rescue': 'search_rescue', 'patrol': 'patrol', 'wildlife': 'wildlife',
        'crowd_control': 'crowd_control', 'ceremonial': 'ceremonial', 'general': 'obedience',
    }
    EXPIRING_DAYS = 60

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='certifications')
    handler = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='team_certifications',
                                help_text='Leave blank for animal-only certificates (e.g. fitness).')
    cert_type = models.CharField('Certification', max_length=20, choices=TYPE_CHOICES)
    certificate_number = models.CharField(max_length=64, blank=True)
    issued_by = models.CharField('Issuing authority', max_length=255, blank=True)
    issued_date = models.DateField()
    expiry_date = models.DateField(db_index=True)
    document = models.FileField(upload_to='certificates/', blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)
    # Last reminder threshold notified ('expiring' / 'expired') so the reminder job never repeats itself.
    reminder_sent = models.CharField(max_length=10, blank=True, editable=False)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='certifications_recorded')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expiry_date']

    def __str__(self):
        return f"{self.animal.name}: {self.get_cert_type_display()} (exp. {self.expiry_date})"

    @property
    def days_left(self):
        return (self.expiry_date - timezone.localdate()).days

    @property
    def state(self):
        days = self.days_left
        if days < 0:
            return 'expired'
        if days <= self.EXPIRING_DAYS:
            return 'expiring'
        return 'valid'

    @property
    def state_label(self):
        return {'expired': 'Expired', 'expiring': 'Expiring', 'valid': 'Valid'}[self.state]

    @property
    def state_badge(self):
        return {'expired': 'tpf-badge-red', 'expiring': 'tpf-badge-amber', 'valid': 'tpf-badge-green'}[self.state]

    @classmethod
    def current(cls, queryset=None):
        """Latest certificate per (animal, type) — older ones are superseded by renewals."""
        qs = queryset if queryset is not None else cls.objects.all()
        latest = (cls.objects.filter(animal=models.OuterRef('animal'), cert_type=models.OuterRef('cert_type'))
                  .order_by('-expiry_date', '-id').values('id')[:1])
        return qs.filter(id=models.Subquery(latest))


class HealthReminderLog(models.Model):
    """Which preventive-care reminders have gone out, so the daily job never repeats one."""
    # Exactly one of these is set: a vet record (vaccination/deworming) or a farrier visit.
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='reminders_sent',
                               null=True, blank=True)
    hoof_record = models.ForeignKey('HoofCareRecord', on_delete=models.CASCADE, related_name='reminders_sent',
                                    null=True, blank=True)
    litter = models.ForeignKey('Litter', on_delete=models.CASCADE, related_name='reminders_sent',
                               null=True, blank=True)
    state = models.CharField(max_length=10)  # 'due_soon' | 'overdue'
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['record', 'state'], name='one_reminder_per_record_state'),
            models.UniqueConstraint(fields=['hoof_record', 'state'], name='one_reminder_per_hoof_record_state'),
            models.UniqueConstraint(fields=['litter', 'state'], name='one_reminder_per_litter_state'),
        ]


# ------------------------------
# Horse care: farrier, tack, housing
# ------------------------------

class HoofCareRecord(models.Model):
    DEFAULT_INTERVAL_DAYS = 42  # typical trim / reshoe cycle

    SERVICE_CHOICES = [
        ('trim', 'Trim'),
        ('full_shoe', 'Full set of shoes'),
        ('front_shoes', 'Front shoes only'),
        ('reset', 'Reset existing shoes'),
        ('corrective', 'Corrective / remedial shoeing'),
        ('treatment', 'Hoof treatment (abscess, thrush)'),
        ('inspection', 'Inspection only'),
    ]
    HOOVES_CHOICES = [
        ('all', 'All four'), ('front', 'Both front'), ('hind', 'Both hind'),
        ('lf', 'Left fore'), ('rf', 'Right fore'), ('lh', 'Left hind'), ('rh', 'Right hind'),
    ]
    CONDITION_CHOICES = [
        ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor - needs attention'), ('lame', 'Lame'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='hoof_records',
                               limit_choices_to={'species': 'horse'})
    date = models.DateField()
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    hooves = models.CharField(max_length=10, choices=HOOVES_CHOICES, default='all')
    farrier = models.CharField(max_length=255, help_text='Farrier name or firm.')
    condition = models.CharField('Hoof condition', max_length=10, choices=CONDITION_CHOICES, default='good')
    notes = models.TextField(blank=True)
    next_due = models.DateField('Next farrier visit', null=True, blank=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='hoof_records_logged')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.animal.name}: {self.get_service_display()} ({self.date})"

    @property
    def condition_badge(self):
        return {'good': 'tpf-badge-green', 'fair': 'tpf-badge-blue', 'poor': 'tpf-badge-amber',
                'lame': 'tpf-badge-red'}.get(self.condition, '')


class TackItem(models.Model):
    INSPECTION_INTERVAL_DAYS = 90

    TYPE_CHOICES = [
        ('saddle', 'Saddle'), ('bridle', 'Bridle'), ('bit', 'Bit'), ('girth', 'Girth'),
        ('saddle_pad', 'Saddle pad / numnah'), ('breastplate', 'Breastplate'), ('halter', 'Head collar / halter'),
        ('lead_rope', 'Lead rope'), ('rug', 'Rug / blanket'), ('boots', 'Boots / bandages'),
        ('riot_gear', 'Riot gear (visor, shields)'), ('ceremonial', 'Ceremonial regalia'), ('other', 'Other'),
    ]
    CONDITION_CHOICES = [
        ('good', 'Good'), ('fair', 'Fair'), ('needs_repair', 'Needs repair'), ('condemned', 'Condemned'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='tack_items')
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    asset_tag = models.CharField('Asset tag', max_length=64, blank=True,
                                 help_text='Stamped / engraved inventory number.')
    description = models.CharField(max_length=255, blank=True, help_text='Make, model, colour.')
    size = models.CharField(max_length=32, blank=True)
    assigned_horse = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='tack_items', limit_choices_to={'species': 'horse'})
    condition = models.CharField(max_length=15, choices=CONDITION_CHOICES, default='good')
    last_inspected = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField('In service', default=True, help_text='Untick when written off or disposed of.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['item_type', 'asset_tag']

    def __str__(self):
        return f"{self.get_item_type_display()} {self.asset_tag}".strip()

    @property
    def next_inspection(self):
        return self.last_inspected + timedelta(days=self.INSPECTION_INTERVAL_DAYS) if self.last_inspected else None

    @property
    def inspection_overdue(self):
        return self.next_inspection is None or self.next_inspection < timezone.localdate()

    @property
    def needs_attention(self):
        return self.condition in ('needs_repair', 'condemned') or self.inspection_overdue

    @property
    def condition_badge(self):
        return {'good': 'tpf-badge-green', 'fair': 'tpf-badge-blue', 'needs_repair': 'tpf-badge-amber',
                'condemned': 'tpf-badge-red'}.get(self.condition, '')


class HousingUnit(models.Model):
    KIND_CHOICES = [
        ('stall', 'Stable stall'), ('paddock', 'Paddock'), ('kennel', 'Kennel'),
        ('isolation', 'Isolation / sick bay'), ('other', 'Other'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='housing_units')
    name = models.CharField(max_length=100, help_text='e.g. Stable Block A, Stall 3')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    capacity = models.PositiveSmallIntegerField(default=1)
    notes = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['kind', 'name']
        constraints = [models.UniqueConstraint(fields=['branch', 'name'], name='unique_housing_name_per_branch')]

    def __str__(self):
        return self.name


class HousingAssignment(models.Model):
    """Where an animal is kept. Open-ended (no end_date) means its current place."""
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='housing_assignments')
    unit = models.ForeignKey(HousingUnit, on_delete=models.PROTECT, related_name='assignments')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    moved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='housing_moves')
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-start_date', '-id']
        constraints = [
            models.UniqueConstraint(fields=['animal'], condition=models.Q(end_date__isnull=True),
                                    name='one_current_housing_per_animal'),
        ]

    def __str__(self):
        return f"{self.animal.name} in {self.unit.name}"


# ------------------------------
# Stores: feed, medicine and consumables
# ------------------------------

class StockItem(models.Model):
    EXPIRY_WARNING_DAYS = 60

    CATEGORY_CHOICES = [
        ('dog_feed', 'Dog feed'), ('horse_feed', 'Horse feed / hay'), ('supplement', 'Supplement'),
        ('medicine', 'Medicine'), ('vaccine', 'Vaccine'), ('dewormer', 'Dewormer'),
        ('consumable', 'Medical consumable'), ('bedding', 'Bedding'), ('other', 'Other'),
    ]
    MEDICAL_CATEGORIES = ('medicine', 'vaccine', 'dewormer', 'consumable')
    UNIT_CHOICES = [
        ('kg', 'kg'), ('bag', 'bags'), ('bale', 'bales'), ('litre', 'litres'), ('tablet', 'tablets'),
        ('dose', 'doses'), ('vial', 'vials'), ('ml', 'ml'), ('piece', 'pieces'), ('box', 'boxes'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='stock_items')
    name = models.CharField(max_length=150, help_text='e.g. Royal Canin Working Dog 20 kg, Rabies vaccine (Nobivac)')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                        help_text='Alert when stock falls to this level or below.')
    reorder_quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                           help_text='Usual quantity to order.')
    supplier = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField('In use', default=True)
    low_stock_notified = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        constraints = [models.UniqueConstraint(fields=['branch', 'name'], name='unique_stock_item_per_branch')]

    def __str__(self):
        return self.name

    @property
    def on_hand(self):
        # Views annotate `stock_on_hand` to avoid a query per row; fall back to a live sum.
        cached = getattr(self, 'stock_on_hand', None)
        if cached is not None:
            return cached
        return self.movements.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def level(self):
        on_hand = self.on_hand
        if on_hand <= 0:
            return 'out'
        if on_hand <= self.reorder_level:
            return 'low'
        return 'ok'

    @property
    def level_label(self):
        return {'out': 'Out of stock', 'low': 'Low', 'ok': 'In stock'}[self.level]

    @property
    def level_badge(self):
        return {'out': 'tpf-badge-red', 'low': 'tpf-badge-amber', 'ok': 'tpf-badge-green'}[self.level]

    def expiring_batches(self):
        """Received batches whose expiry is past or within the warning window (only while stock remains)."""
        if self.on_hand <= 0:
            return self.movements.none()
        horizon = timezone.localdate() + timedelta(days=self.EXPIRY_WARNING_DAYS)
        return self.movements.filter(kind='received', expiry_date__isnull=False,
                                     expiry_date__lte=horizon).order_by('expiry_date')


class StockMovement(models.Model):
    """Every change to stock. quantity is signed: + into stores, - out of stores."""
    KIND_CHOICES = [
        ('received', 'Received'), ('issued', 'Issued'), ('wasted', 'Wasted / expired'),
        ('adjustment', 'Stock-take adjustment'),
    ]
    OUTGOING = ('issued', 'wasted')

    item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    kind = models.CharField(max_length=12, choices=KIND_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='stock_issued', help_text='Animal the stock was used for.')
    batch_number = models.CharField(max_length=64, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=128, blank=True, help_text='Delivery note, LPO, medical record...')
    notes = models.CharField(max_length=255, blank=True)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='stock_used')
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='stock_movements')
    expiry_notified = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.get_kind_display()} {self.quantity} {self.item.get_unit_display()} {self.item.name}"

    @property
    def is_expired(self):
        return self.expiry_date is not None and self.expiry_date < timezone.localdate()


# ------------------------------
# Branch transfers
# ------------------------------

class AnimalTransfer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Awaiting approval'), ('approved', 'Approved - in transit'), ('completed', 'Received'),
        ('rejected', 'Rejected'), ('cancelled', 'Cancelled'),
    ]
    OPEN_STATUSES = ('pending', 'approved')

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='transfers')
    from_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_out')
    to_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_in')
    reason = models.TextField()
    planned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)

    requested_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='transfers_requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='transfers_decided')
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.CharField(max_length=255, blank=True)
    received_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transfers_received')
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        constraints = [
            models.UniqueConstraint(fields=['animal'], condition=models.Q(status__in=('pending', 'approved')),
                                    name='one_open_transfer_per_animal'),
        ]

    def __str__(self):
        return f"{self.animal.name}: {self.from_branch} -> {self.to_branch} ({self.get_status_display()})"

    @property
    def status_badge(self):
        return {'pending': 'tpf-badge-amber', 'approved': 'tpf-badge-blue', 'completed': 'tpf-badge-green',
                'rejected': 'tpf-badge-red', 'cancelled': ''}.get(self.status, '')


# ------------------------------
# Breeding
# ------------------------------

class Litter(models.Model):
    """A mating and its outcome (a litter of puppies or a foal)."""
    GESTATION_DAYS = {'dog': 63, 'horse': 340}
    STATUS_CHOICES = [
        ('mated', 'Mated'), ('pregnant', 'Pregnancy confirmed'), ('born', 'Born'),
        ('failed', 'Not pregnant / lost'),
    ]
    OPEN_STATUSES = ('mated', 'pregnant')

    dam = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='litters_as_dam',
                            limit_choices_to={'sex': 'female'})
    sire = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True, related_name='litters_as_sire',
                             limit_choices_to={'sex': 'male'})
    external_sire = models.CharField('Outside sire', max_length=255, blank=True,
                                     help_text='Name / registration if the sire is not a TPF animal.')
    mating_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='mated', db_index=True)
    birth_date = models.DateField(null=True, blank=True)
    born_alive = models.PositiveSmallIntegerField(null=True, blank=True)
    stillborn = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='litters_recorded')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-mating_date', '-id']

    def __str__(self):
        return f"{self.dam.name} x {self.sire_name} ({self.mating_date})"

    @property
    def sire_name(self):
        return self.sire.name if self.sire else (self.external_sire or 'Unknown sire')

    @property
    def status_badge(self):
        return {'mated': 'tpf-badge-blue', 'pregnant': 'tpf-badge-purple', 'born': 'tpf-badge-green',
                'failed': ''}.get(self.status, '')

    def save(self, *args, **kwargs):
        if self.mating_date and not self.expected_date:
            days = self.GESTATION_DAYS.get(self.dam.species)
            if days:
                self.expected_date = self.mating_date + timedelta(days=days)
        super().save(*args, **kwargs)
