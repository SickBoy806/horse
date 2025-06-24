from django.db import models
from django.conf import settings
from veterinarian_dashboard.models import Animal


class AnimalLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    ACTIVITY_TYPES = [
        ('feeding', 'Feeding'),
        ('cleaning', 'Cleaning'),
        ('exercise', 'Exercise'),
        ('health_obs', 'Health Observation'),
        ('incident', 'Incident'),
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    notes = models.TextField()

    def __str__(self):
        return f"{self.animal.name} - {self.activity_type} by {self.user.username} on {self.date}"


class DailyActivityReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branch = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    summary = models.TextField()
    issues_faced = models.TextField(blank=True)
    hours_worked = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"Report by {self.user.username} on {self.date}"


class UserMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} - {self.subject}"


class UserNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"To {self.user.username} - {self.message}"


class EmergencyIncident(models.Model):
    INCIDENT_TYPES = [
        ('injury', 'Injury'),
        ('escape', 'Escape'),
        ('illness', 'Illness'),
        ('aggression', 'Aggression'),
        ('other', 'Other'),
    ]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    animal = models.ForeignKey('veterinarian_dashboard.Animal', on_delete=models.CASCADE)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES)
    description = models.TextField()
    photo = models.ImageField(upload_to='emergency_photos/', blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.incident_type.title()} - {self.animal.name} ({self.date_reported.date()})"


class EquipmentLog(models.Model):
    EQUIPMENT_CHOICES = [
        ('leash', 'Leash'),
        ('feeding_kit', 'Feeding Kit'),
        ('first_aid', 'First Aid Kit'),
        ('cleaning', 'Cleaning Tools'),
        ('training_gear', 'Training Gear'),
        ('other', 'Other'),
    ]
    ACTION_CHOICES = [
        ('check_out', 'Checked Out'),
        ('check_in', 'Returned'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    equipment = models.CharField(max_length=100, choices=EQUIPMENT_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_equipment_display()} - {self.get_action_display()}"


class SupportRequest(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.status})"
