from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MedicalRecordForm
from .models import MedicalRecord, Animal
from .models import VetTask
from .forms import VetTaskForm
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.db.models import Count, Avg, Q
from core.models import Animal, Task
from .models import MedicalRecord
from accounts.models import CustomUser
from datetime import timedelta


@login_required
def vet_dashboard(request, branch):
    print(f"User branch: {request.user.branch} | URL branch: {branch} | User role: {request.user.role}")

    if request.user.role != 'veterinarian' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    records = MedicalRecord.objects.filter(vet=request.user).order_by('-date')[:5]
    return render(request, 'veterinarian_dashboard/dashboard.html', {
        'branch': branch,
        'records': records,
    })


@login_required
def add_medical_record(request, branch):
    print(f"Add Record Check => User role: {request.user.role} | User branch: {request.user.branch} | URL branch: {branch}")

    if request.user.role != 'veterinarian' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    form = MedicalRecordForm()
    form.fields['animal'].queryset = Animal.objects.filter(branch=branch)

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.vet = request.user
            record.save()
            return redirect('vet_dashboard', branch=branch)

    return render(request, 'veterinarian_dashboard/add_medical_record.html', {
        'form': form,
        'branch': branch
    })


@login_required
def medical_records_list(request, branch):
    print(f"Medical Records List Check => User role: {request.user.role} | User branch: {request.user.branch} | URL branch: {branch}")

    if request.user.role != 'veterinarian' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    records = MedicalRecord.objects.filter(vet=request.user).order_by('-date')
    return render(request, 'veterinarian_dashboard/medical_records_list.html', {
        'records': records,
        'branch': branch,
    })

@login_required
def assign_task(request, branch):
    # ✅ Move prints before the condition
    print("User role:", request.user.role)
    print("User branch:", request.user.branch)
    print("URL branch:", branch)

    # ❗️Fix: Ensure role is correctly matched (e.g., vet vs. veterinarian)
    if request.user.role.lower() not in ['vet', 'veterinarian'] or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    form = VetTaskForm()
    form.fields['animal'].queryset = Animal.objects.filter(branch__iexact=branch)
    form.fields['assigned_to'].queryset = CustomUser.objects.filter(
        branch__iexact=branch, role__in=['staff', 'user']
    )

    if request.method == 'POST':
        form = VetTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            return redirect('vet_task_list', branch=branch)

    return render(request, 'veterinarian_dashboard/assign_task.html', {
        'form': form,
        'branch': branch
    })


@login_required
def vet_task_list(request, branch):
    if request.user.role.lower() != 'vet' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(assigned_by=request.user).order_by('-date_assigned')
    return render(request, 'veterinarian_dashboard/task_list.html', {'tasks': tasks, 'branch': branch})


@login_required
def vet_task_detail(request, branch, task_id):
    task = get_object_or_404(VetTask, id=task_id, assigned_by=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            task.status = 'approved'
        elif action == 'reject':
            task.status = 'rejected'
        task.save()
        return redirect('vet_task_list', branch=branch)

    return render(request, 'veterinarian_dashboard/task_detail.html', {'task': task, 'branch': branch})

@login_required
def search_medical_records(request, branch):
    if request.user.role != 'veterinarian' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    query = request.GET.get('q', '')
    records = MedicalRecord.objects.filter(vet=request.user)
    if query:
        records = records.filter(description__icontains=query)  # or other fields you want to search by

    return render(request, 'veterinarian_dashboard/search_medical_records.html', {
        'records': records,
        'branch': branch,
        'query': query,
    })

@login_required
def pending_tasks(request, branch):
    if request.user.role != 'veterinarian' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(assigned_by=request.user, status='pending').order_by('-date_assigned')
    return render(request, 'veterinarian_dashboard/pending_tasks.html', {'tasks': tasks, 'branch': branch})

@login_required
def completed_tasks(request, branch):
    if request.user.role != 'veterinarian' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(assigned_by=request.user, status='completed').order_by('-date_assigned')
    return render(request, 'veterinarian_dashboard/completed_tasks.html', {'tasks': tasks, 'branch': branch})

from .models import Patient
from .forms import PatientForm

@login_required
def add_patient(request, branch):
    if request.user.branch.lower() != branch.lower() or request.user.role != 'veterinarian':
        return render(request, 'errors/unauthorized.html', status=403)

    form = PatientForm()
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.branch = branch  # Set branch from URL param
            patient.save()
            return redirect('patient_list', branch=branch)  # Make sure you have patient_list URL/view
    return render(request, 'veterinarian_dashboard/add_patient.html', {
        'form': form,
        'branch': branch,
    })

def patient_list(request, branch):
    patients = Patient.objects.filter(branch=branch)
    return render(request, 'veterinarian_dashboard/patient_list.html', {
        'patients': patients,
        'branch': branch,
    })

def search_patients(request, branch):
    query = request.GET.get('q', '')
    patients = Animal.objects.filter(branch=branch)
    if query:
        patients = patients.filter(name__icontains=query)
    context = {
        'branch': branch,
        'patients': patients,
        'query': query,
    }
    return render(request, 'veterinarian_dashboard/search_patients.html', context)

def analytics_dashboard(request, branch):
    # Filter animals by branch
    animals = Animal.objects.filter(branch__iexact=branch)
    tasks = VetTask.objects.filter(animal__branch__iexact=branch)

    context = {
        'branch': branch,
        'total_patients': animals.count(),
        'active_cases': tasks.filter(status='pending').count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'completed_tasks': tasks.filter(status='completed').count(),
    }
    return render(request, 'veterinarian_dashboard/analytics_dashboard.html', context)

def performance_reports(request, branch):
    # Filter by current vet and branch
    vet = request.user
    branch_lower = branch.lower()

    # Total patients for this vet at this branch
    total_patients = Animal.objects.filter(branch__iexact=branch_lower, assigned_vet=vet).count()

    # Task stats
    tasks = VetTask.objects.filter(assigned_to=vet, animal__branch__iexact=branch_lower)
    tasks_completed = tasks.filter(status='completed').count()
    tasks_pending = tasks.filter(status='pending').count()

    # Average days between task assignment and due date (for completed tasks)
    avg_response_time = tasks.filter(status='completed').annotate(
        response_days=Avg(Q(due_date=None) | Q(date_assigned=None))
    ).aggregate(avg=Avg('due_date'))['avg']

    context = {
        'branch': branch,
        'total_patients': total_patients,
        'tasks_completed': tasks_completed,
        'tasks_pending': tasks_pending,
        'average_response_time': avg_response_time if avg_response_time else "N/A",
    }

    return render(request, 'veterinarian_dashboard/performance_reports.html', context)

@login_required
def vet_settings(request, branch):
    return render(request, 'veterinarian_dashboard/vet_settings.html', {
        'branch': branch
    })

@login_required
def help_support(request, branch):
    return render(request, 'veterinarian_dashboard/help_support.html', {
        'branch': branch
    })

