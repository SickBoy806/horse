from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm, AssignTaskForm
from accounts.models import CustomUser
from core.models import Task


# 🔐 Admin Role Check
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# 📊 Admin Dashboard
@login_required
def admin_dashboard(request, branch):
    if request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    context = {
        'branch': request.user.branch.title()
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

# 👤 Create User
@login_required
def create_user(request, branch):
    if request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.branch = request.user.branch  # force same branch
            user.save()
            return redirect('admin_dashboard', branch=branch)
    else:
        form = CreateUserForm()

    return render(request, 'admin_dashboard/create_user.html', {
        'form': form,
        'branch': request.user.branch.title()
    })

# ✅ Assign Task
@login_required
def assign_task(request, branch):
    if request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = AssignTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            return redirect('admin_dashboard', branch=branch)
    else:
        form = AssignTaskForm()

    return render(request, 'admin_dashboard/assign_task.html', {
        'form': form,
        'branch': request.user.branch.title()
    })

# ✅ Approve Activities
@login_required
def approve_activities(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return render(request, 'admin_dashboard/approve_activities.html', {
        'branch': request.user.branch.title()
    })

# ✅ Admin Reports (placeholder)
@login_required
def admin_reports(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return HttpResponse(f"Admin reports for branch: {branch} (placeholder view)")

# ✅ Animal List (placeholder)
@login_required
def animal_list(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return HttpResponse(f"Animal list for branch: {branch} (placeholder view)")

# ✅ User List
@login_required
def user_list(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    users = CustomUser.objects.filter(branch=request.user.branch).exclude(username=request.user.username)

    return render(request, 'admin_dashboard/user_list.html', {
        'users': users,
        'branch': request.user.branch.title()
    })
