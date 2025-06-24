from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

BRANCHES = [
    ('HQ', 'HQ'),
    ('Dodoma', 'Dodoma'),
    ('Iringa', 'Iringa'),
    ('TPS_Moshi', 'TPS Moshi'),
]

ROLES = [
    ('superadmin', 'Super Admin'),
    ('admin', 'Admin'),
    ('veterinarian', 'Veterinarian'),
    ('staff', 'Staff'),
    ('user', 'User'),
]

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLES)
    branch = models.CharField(max_length=20, choices=BRANCHES)