from django.db import models
from accounts.models import CustomUser
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_by = models.ForeignKey(CustomUser, related_name='tasks_given', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(CustomUser, related_name='tasks_received', on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
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
    force_number = models.CharField(max_length=255, default='some_default_value')
    owner_name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='', null=True, blank=True)


    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True)

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


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    subject = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branch = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.id} - {self.subject}"


class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    replied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.replied_by} on ticket #{self.ticket.id}"

class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('assign', 'Assign Task'),
        ('approve', 'Approve Report'),
        ('error', 'Error'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    branch = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.user.username} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class Report(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_created = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports'
    )

    def __str__(self):
        return self.title

@login_required
def animal_list(request):
    if request.user.role not in ['admin', 'veterinarian', 'superadmin', 'user']:
        return render(request, 'errors/unauthorized.html', status=403)

    branch = request.user.branch

    animals = Animal.objects.filter(
        assigned_users__branch=branch
    ).distinct().order_by('-id')

    search = request.GET.get("q")
    if search:
        animals = animals.filter(
            Q(name__icontains=search) | Q(species__icontains=search)
        )

    paginator = Paginator(animals, 10)
    page = request.GET.get("page")
    paginated_animals = paginator.get_page(page)

    return render(request, 'core/animal_list.html', {
        'animals': paginated_animals,
        'search': search,
    })



@login_required
def view_animal_detail(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)

    # ✅ Check if user belongs to branch via assigned_users
    if request.user.role != 'superadmin' and not animal.assigned_users.filter(branch=request.user.branch).exists():
        return render(request, 'errors/unauthorized.html', status=403)

    assigned_users = animal.assigned_users.all()

    return render(request, 'core/view_animal_detail.html', {
        'animal': animal,
        'assigned_users': assigned_users,
    })