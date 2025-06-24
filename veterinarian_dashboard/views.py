from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MedicalRecordForm
from .models import MedicalRecord, Animal
from .models import VetTask
from .forms import VetTaskForm
from django.shortcuts import get_object_or_404


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
    if request.user.role != 'veterinarian' or request.user.branch != branch:
        return render(request, 'errors/unauthorized.html', status=403)

    form = VetTaskForm()
    form.fields['animal'].queryset = Animal.objects.filter(branch=branch)
    form.fields['assigned_to'].queryset = CustomUser.objects.filter(
        branch=branch, role__in=['staff', 'user']
    )

    if request.method == 'POST':
        form = VetTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            return redirect('vet_task_list', branch=branch)

    return render(request, 'veterinarian_dashboard/assign_task.html', {'form': form, 'branch': branch})


@login_required
def vet_task_list(request, branch):
    if request.user.role != 'veterinarian' or request.user.branch != branch:
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

