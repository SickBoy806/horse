from django.db import models
from accounts.models import CustomUser
from core.models import Animal  # Adjust if your Animal model is elsewhere

class VetTask(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    due_date = models.DateField()

    def __str__(self):
        return self.title

class MedicalRecord(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    veterinarian = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='admin_medical_records')
    diagnosis = models.TextField()
    treatment = models.TextField()
    document = models.FileField(upload_to='medical_documents/', null=True, blank=True)
    date_recorded = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Medical Record for {self.animal} on {self.date_recorded}"
