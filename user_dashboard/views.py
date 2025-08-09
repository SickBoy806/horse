from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from core.models import Branch
from core.utils import normalize_branch_name
from django.db.models import Q




from veterinarian_dashboard.models import VetTask, Animal
from core.models import Notification
from .models import (
    AnimalLog,
    DailyActivityReport,
    UserMessage,
    UserNotification,
    EmergencyIncident,
    SupportRequest,
    EquipmentLog
)
from .forms import (
    AnimalLogForm,
    DailyActivityReportForm,
    UserMessageForm,
    EmergencyIncidentForm,
    SupportRequestForm,
    EquipmentLogForm
)


@login_required
def user_dashboard(request, branch):
    # Ensure user role and branch match
    if request.user.role.lower() != 'user' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    # Fetch latest 5 tasks assigned to user
    tasks = VetTask.objects.filter(assigned_to=request.user).order_by('-date_assigned')[:5]

    # Fetch latest 5 animals assigned to user
    animals = Animal.objects.filter(assigned_users=request.user)[:5]

    # Fetch latest 5 unread notifications
    notifications = UserNotification.objects.filter(user=request.user, is_read=False)[:5]

    # Count unread notifications
    unread_notifications_count = notifications.count()

    return render(request, 'user_dashboard/dashboard.html', {
        'branch': branch.lower(),
        'tasks': tasks,
        'animals': animals,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    })


@login_required
def user_tasks(request, branch):
    tasks = VetTask.objects.filter(assigned_to=request.user).order_by('-date_assigned')
    return render(request, 'user_dashboard/tasks.html', {
        'branch': branch,
        'tasks': tasks,
    })


@login_required
def update_task_status(request, branch, task_id):
    task = get_object_or_404(VetTask, id=task_id, assigned_to=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['in_progress', 'completed']:
            task.status = new_status
            task.save()
            messages.success(request, "Task status updated successfully.")
        else:
            messages.error(request, "Invalid status.")
    return redirect('user_tasks', branch=branch)


@login_required
def animal_logs(request, branch):
    if request.user.role.lower() != 'user' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    logs = AnimalLog.objects.filter(user=request.user).order_by('-date')
    form = AnimalLogForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.user = request.user
        log.save()
        return redirect('animal_logs', branch=branch)

    return render(request, 'user_dashboard/animal_logs.html', {
        'form': form,
        'logs': logs,
        'branch': branch
    })


@login_required
def report_activity(request, branch):
    if request.user.role.lower() != 'user' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    reports = DailyActivityReport.objects.filter(user=request.user).order_by('-date')
    form = DailyActivityReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.user = request.user
        report.branch = branch
        report.save()
        return redirect('report_activity', branch=branch)

    return render(request, 'user_dashboard/report_activity.html', {
        'form': form,
        'reports': reports,
        'branch': branch,
    })


@login_required
def user_messages(request, branch):
    if request.user.role.lower() != 'user' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    inbox = UserMessage.objects.filter(receiver=request.user).order_by('-timestamp')
    form = UserMessageForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        message.sender = request.user
        message.save()
        return redirect('user_messages', branch=branch)

    return render(request, 'user_dashboard/user_messages.html', {
        'inbox': inbox,
        'form': form,
        'branch': branch
    })


@login_required
def notifications_view(request, branch):
    notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')
    if request.method == 'POST':
        notif_id = request.POST.get("notif_id")
        if notif_id:
            notif = get_object_or_404(UserNotification, id=notif_id, user=request.user)
            notif.is_read = True
            notif.save()
        return redirect('notifications_view', branch=branch)

    return render(request, 'user_dashboard/notifications.html', {
        'notifications': notifications,
        'branch': branch,
    })


@login_required
def api_unread_notifications_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def assigned_animals(request, branch):
    # Check user role and branch access
    if request.user.role.lower() != 'user' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    # Get the Branch instance by name (case-insensitive)
    branch_obj = get_object_or_404(Branch, name__iexact=branch)

    # Filter animals by assigned_users and branch instance
    animals = Animal.objects.filter(assigned_users=request.user, branch=branch_obj)

    return render(request, 'user_dashboard/assigned_animals.html', {
        'animals': animals,
        'branch': branch_obj
    })


@login_required
def report_emergency(request, branch):
    if request.user.role.lower() != 'user' or normalize_branch_name(request.user.branch.name) != normalize_branch_name(branch):
        return render(request, 'errors/unauthorized.html', status=403)

    form = EmergencyIncidentForm(request.POST or None, request.FILES or None)
    form.fields['animal'].queryset = Animal.objects.filter(assigned_users=request.user)

    if request.method == 'POST' and form.is_valid():
        incident = form.save(commit=False)
        incident.reporter = request.user
        incident.save()
        return redirect('report_emergency', branch=branch)

    incidents = EmergencyIncident.objects.filter(reporter=request.user).order_by('-date_reported')

    return render(request, 'user_dashboard/report_emergency.html', {
        'form': form,
        'incidents': incidents,
        'branch': branch
    })


@login_required
def equipment_log_view(request, branch):
    if request.user.role.lower() != 'user' or normalize_branch_name(request.user.branch.name) != normalize_branch_name(branch):
        return render(request, 'errors/unauthorized.html', status=403)

    form = EquipmentLogForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.user = request.user
        log.save()
        return redirect('equipment_log_view', branch=branch)

    logs = EquipmentLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'user_dashboard/equipment_log.html', {
        'form': form,
        'logs': logs,
        'branch': branch
    })



@login_required
def support_request_view(request, branch):
    user = request.user
    branch_name = branch  # URL param branch (string)

    if user.role == 'superadmin':
        requests = SupportRequest.objects.all()
    elif user.role == 'admin':
        # Admin sees all requests in their branch
        requests = SupportRequest.objects.filter(branch=user.branch)
    else:
        # Normal user sees requests created by or assigned to them in their branch
        requests = SupportRequest.objects.filter(
            Q(created_by=user) | Q(assigned_to=user),
            branch=user.branch
        )

    requests = requests.order_by('-created_at')

    return render(request, 'user_dashboard/support_request_list.html', {
        'requests': requests,
        'branch': branch_name,  # pass it as 'branch' to match template usage
    })
