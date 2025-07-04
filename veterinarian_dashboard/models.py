from django.db import models
from accounts.models import CustomUser

class Animal(models.Model):
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('horse', 'Horse')
    ]
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=10, choices=SPECIES_CHOICES)
    branch = models.CharField(max_length=20)
    age = models.PositiveIntegerField()
    assigned_vet = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='animal_photos/', null=True, blank=True)
    assigned_users = models.ManyToManyField(CustomUser, blank=True, related_name='vet_assigned_animals')

    def __str__(self):
        return f"{self.name} ({self.species})"

class MedicalRecord(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    diagnosis = models.TextField()
    treatment = models.TextField()
    vet = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vet_medical_records')
    document = models.FileField(upload_to='medical_reports/', blank=True, null=True)

    def __str__(self):
        return f"{self.animal.name} - {self.date}"

class VetTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_vet_tasks_assigned')
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='tasks_created')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_assigned = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()

    def __str__(self):
        return self.title

# Move Patient model outside of VetTask class
class Patient(models.Model):
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    breed = models.CharField(max_length=50, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    branch = models.CharField(max_length=100)

    def __str__(self):
        return self.name
