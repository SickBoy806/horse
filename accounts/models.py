from django.contrib.auth.models import AbstractUser
from django.db import models

# Define the fixed branches
BRANCHES = [
    ('Dodoma', 'Dodoma'),
    ('Iringa', 'Iringa'),
    ('HQ', 'HQ'),
    ('Tps_Moshi', 'Tps Moshi'),
]

# Define roles as you need
ROLES = [
    ('superadmin', 'Super Admin'),
    ('admin', 'Admin'),
    ('veterinarian', 'Veterinarian'),
    ('staff', 'Staff'),
    ('user', 'User'),
]

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=ROLES)
    branch = models.CharField(max_length=30, choices=BRANCHES)

    def __str__(self):
        return self.username
