from django.db import models
from accounts.models import CustomUser
# Remove this line: from django.contrib.auth.models import User

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_by = models.ForeignKey(CustomUser, related_name='tasks_given', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(CustomUser, related_name='tasks_received', on_delete=models.CASCADE)
    branch = models.CharField(max_length=100, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Animal(models.Model):
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    owner_name = models.CharField(max_length=255)
    branch = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='animal_photos/', null=True, blank=True)


    assigned_users = models.ManyToManyField(CustomUser, blank=True, related_name='core_assigned_animals')


    def __str__(self):
        return f"{self.name} ({self.species})"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Changed from User to CustomUser
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"