from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import TaskForm
from .models import Task

@login_required
def assign_task(request):
    if request.user.role not in ['admin', 'veterinarian']:
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.branch = request.user.branch
            task.save()
            return redirect('dashboard_home')  # or your actual dashboard route
    else:
        form = TaskForm(user=request.user)

    return render(request, 'tasks/assign_task.html', {'form': form})