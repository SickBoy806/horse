from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from core.models import Branch
from core.models import MedicalRecord

from .forms import CustomUserForm, AssignTaskForm, VetTaskForm, SupportTicketForm, TicketReplyForm
from accounts.models import CustomUser
from core.models import (
    VetTask, Animal, DailyActivityReport, AnimalLog,
    SupportTicket, TicketReply, EmergencyIncident, Branch, Message,
    EquipmentLog, Report,
)
from core.utils import log_action, create_notification, can_access_branch


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
def admin_dashboard(request, branch):
    if request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = request.user.branch
    context = {
        'branch': branch_obj.name.title(),
        'total_users': CustomUser.objects.filter(branch=branch_obj).count(),
        'pending_tasks': VetTask.objects.filter(branch=branch_obj, status='pending').count(),
        'total_animals': Animal.objects.filter(branch=branch_obj).count(),
        'reports_today': DailyActivityReport.objects.filter(
            branch=branch_obj, date=timezone.now().date()
        ).count(),
        'open_tickets': SupportTicket.objects.filter(
            created_by__branch=branch_obj, status='open'
        ).count(),
        'closed_tickets': SupportTicket.objects.filter(
            created_by__branch=branch_obj, status='closed'
        ).count(),
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

# 👤 Create User
@login_required
def create_user(request, branch):
    if request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.branch = request.user.branch
            user.save()
            return redirect('admin_dashboard', branch=branch)
    else:
        form = CustomUserForm()

    return render(request, 'admin_dashboard/create_user.html', {
        'form': form,
        'branch': request.user.branch.name.title()
    })

# ✅ Assign Task
@login_required
def task_assign(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = request.user.branch
    form = VetTaskForm(request.POST or None, branch=branch)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.branch = branch_obj
        task.save()
        return redirect('admin_task_list', branch=branch)

    return render(request, 'admin_dashboard/task_form.html', {'form': form, 'branch': branch, 'title': 'Assign Task'})

# List Tasks
@login_required
def task_list(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = request.user.branch
    tasks = VetTask.objects.filter(branch=branch_obj).order_by('-created_at')
    return render(request, 'admin_dashboard/task_list.html', {'tasks': tasks, 'branch': branch})

# Task Detail
@login_required
def task_detail(request, branch, task_id):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = request.user.branch
    task = get_object_or_404(VetTask, id=task_id, branch=branch_obj)
    return render(request, 'admin_dashboard/task_detail.html', {'task': task, 'branch': branch})

# ✅ Approve Activities
@login_required
def approve_activities(request, branch):
    if not is_admin(request.user) or request.user.branch.name.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return render(request, 'admin_dashboard/approve_activities.html', {
        'branch': request.user.branch.name.title()
    })

# ✅ Admin Reports (placeholder)
@login_required
def admin_reports(request, branch, task_id=None):
    if not is_admin(request.user) or request.user.branch.name.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    reports = (DailyActivityReport.objects.filter(branch=request.user.branch)
               .select_related('user').order_by('-date'))
    return render(request, 'admin_dashboard/admin_reports.html', {'reports': reports, 'branch': branch})

# ✅ Animal List (placeholder)
@login_required
def animal_list(request, branch):
    if not is_admin(request.user) or request.user.branch.name.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return admin_animals(request, branch)

# List users
def admin_user_list(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = Branch.objects.filter(name__iexact=branch).first()
    if not branch_obj:
        return render(request, 'errors/not_found.html', status=404)

    users = CustomUser.objects.filter(branch=branch_obj)
    return render(request, 'admin_dashboard/admin_user_list.html', {
        'users': users,
        'branch': branch,
    })

# Add user
def user_add(request, branch):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    form = CustomUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data['password']:
            user.password = make_password(form.cleaned_data['password'])
        user.save()
        return redirect('admin_user_list', branch=branch)

    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'branch': branch, 'title': 'Add User'})

# Edit user
def user_edit(request, branch, user_id):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    user = get_object_or_404(CustomUser, id=user_id, branch__name__iexact=branch)
    form = CustomUserForm(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data['password']:
            user.password = make_password(form.cleaned_data['password'])
        user.save()
        return redirect('admin_user_list', branch=branch)

    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'branch': branch, 'title': 'Edit User'})


# Delete user
@login_required
def user_delete(request, branch, user_id):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    user = get_object_or_404(CustomUser, id=user_id, branch=branch)

    if request.method == 'POST':
        user.delete()
        return redirect('admin_user_list', branch=branch)  # make sure this matches your URL name

    return render(request, 'admin_dashboard/user_confirm_delete.html', {
        'user': user,
        'branch': branch
    })

def reports_view(request, branch):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)
    branch_obj = Branch.objects.filter(name__iexact=branch).first()
    reports = DailyActivityReport.objects.filter(branch=branch_obj).order_by('-date') if branch_obj else []
    return render(request, 'admin_dashboard/admin_reports.html', {'reports': reports, 'branch': branch})

# View animal care logs
def care_logs_view(request, branch):
    logs = AnimalLog.objects.filter(branch=branch, log_type='care').order_by('-date')
    return render(request, 'admin_dashboard/care_logs.html', {'logs': logs, 'branch': branch})

# View incident logs
def incident_logs_view(request, branch):
    logs = AnimalLog.objects.filter(branch=branch, log_type='incident').order_by('-date')
    return render(request, 'admin_dashboard/incident_logs.html', {'logs': logs, 'branch': branch})

def admin_incident_logs(request, branch):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    incidents = EmergencyIncident.objects.filter(animal__branch=request.user.branch).order_by('-date_reported')
    return render(request, 'admin_dashboard/incident_logs.html', {
        'branch': branch,
        'incidents': incidents
    })

@login_required
def admin_care_logs(request, branch):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    logs = AnimalLog.objects.filter(animal__branch=request.user.branch).order_by('-date')
    return render(request, 'admin_dashboard/care_logs.html', {
        'branch': branch,
        'logs': logs,
    })

def admin_support(request, branch):
    if request.user.role != 'admin' and request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)
    tickets = SupportTicket.objects.filter(
        created_by__branch__name__iexact=branch
    ).order_by('-created_at')
    return render(request, 'admin_dashboard/support_list.html', {'tickets': tickets, 'branch': branch})


@login_required
@login_required
def admin_animals(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)
    animals = Animal.objects.filter(branch=request.user.branch)
    return render(request, 'admin_dashboard/admin_animals.html', {
        'animals': animals,
        'branch': branch
    })

@login_required
def support_ticket_list(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized")

    tickets = SupportTicket.objects.filter(created_by__branch=request.user.branch).order_by('-created_at')
    return render(request, 'admin_dashboard/support_list.html', {'tickets': tickets, 'branch': branch})

@login_required
def support_ticket_detail(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    replies = TicketReply.objects.filter(ticket=ticket).order_by('created_at')

    if request.method == 'POST':
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = ticket
            reply.user = request.user
            reply.save()
            ticket.status = 'in_progress'
            ticket.save()
            return redirect('admin_support_detail', branch=branch, ticket_id=ticket.id)
    else:
        form = TicketReplyForm()

    return render(request, 'admin_dashboard/support_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'form': form,
        'branch': branch
    })

@login_required
def close_support_ticket(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    ticket.status = 'closed'
    ticket.save()
    return redirect('admin_support_detail', branch=branch, ticket_id=ticket.id)


@login_required
def notifications(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    from core.models import Notification
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    msgs = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:50]
    # Mark all as read
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    Message.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    return render(request, 'admin_dashboard/notifications.html', {
        'branch': branch,
        'notifs': notifs,
        'msgs': msgs,
    })


@login_required
def admin_medical_records(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    records = MedicalRecord.objects.filter(animal__branch=request.user.branch)
    return render(request, 'admin_dashboard/medical_records_list.html', {
        'records': records,
        'branch': branch,
    })


# admin_dashboard/views.py
@login_required
def admin_equipment_logs(request, branch):
    if request.user.role != 'admin' or request.user.branch.name.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    logs = EquipmentLog.objects.filter(user__branch__name__iexact=branch).order_by('-timestamp')
    return render(request, 'admin_dashboard/equipment_logs.html', {
        'logs': logs,
        'branch': branch,
    })



@login_required
def training_sessions_view(request):
    user = request.user

    # Determine base template
    base_template = "admin_dashboard/base_admin.html"
    sessions = TrainingSession.objects.filter(branch=user.branch).order_by('-date')

    return render(request, "core/training_sessions.html", {
        "sessions": sessions,
        "base_template": base_template,
    })

@login_required
def create_task(request):
    branch = request.user.branch.name.lower() if request.user.branch else ''
    form = VetTaskForm(request.POST or None, branch=branch)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.branch = request.user.branch
        task.save()
        return redirect('admin_dashboard', branch=branch)
    return render(request, 'admin_dashboard/task_form.html', {'form': form, 'branch': branch, 'title': 'Create Task'})


@login_required
def generate_report(request):
    # Generated reports live in the shared Reports page.
    return redirect('reports_list')


@login_required
def settings(request):
    branch = request.user.branch.name.lower() if request.user.branch else ''
    return render(request, 'admin_dashboard/settings.html', {'branch': branch})