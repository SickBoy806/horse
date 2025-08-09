from django.db import models
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
        ('cat', 'Cat'),
        ('other', 'Other'),
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.force_number})"

    class Meta:
        ordering = ['-created_at']


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

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.subject}"

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
    description = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_reports')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='reports')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_created']
