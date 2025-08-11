from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from core.forms import MessageReplyForm
from django.db.models import Q, Avg
from django.utils import timezone
from core.forms import MessageForm, MessageReplyForm, SupportTicketForm
from datetime import datetime, timedelta
from core.models import (
    Notification, Animal, VetTask, Branch, Message, SupportTicket,
    MedicalRecord, EquipmentLog, EmergencyIncident, AnimalLog
)
from accounts.models import CustomUser
from .forms import (
    MedicalRecordForm, VetTaskForm, PatientForm,
    EquipmentLogForm, EmergencyReportForm,
)


def is_authorized_branch(user, branch_name, role=None):
    branch_check = user.branch and user.branch.name.lower() == branch_name.lower()
    if role:
        return branch_check and user.role.lower() == role.lower()
    return branch_check


@login_required
def vet_dashboard(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)

    total_animals = Animal.objects.filter(branch=branch_obj).count()
    total_tasks = VetTask.objects.filter(branch=branch_obj).count()
    total_medical_records = MedicalRecord.objects.filter(animal__branch=branch_obj).count()
    total_notifications = Notification.objects.filter(user__branch=branch_obj).count()

    recent_messages = Message.objects.filter(
        receiver=request.user,
        receiver__branch=branch_obj
    ).order_by("-timestamp")[:5]

    context = {
        "branch": branch_obj.name,
        "total_animals": total_animals,
        "total_tasks": total_tasks,
        "total_medical_records": total_medical_records,
        "total_notifications": total_notifications,
        "recent_messages": recent_messages,
    }

    return render(request, "veterinarian_dashboard/dashboard.html", context)


@login_required
def veterinarian_dashboard_data(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)

    total_animals = Animal.objects.filter(branch=branch_obj).count()
    total_tasks = VetTask.objects.filter(branch=branch_obj).count()
    total_medical_records = MedicalRecord.objects.filter(animal__branch=branch_obj).count()
    total_notifications = Notification.objects.filter(user__branch=branch_obj).count()

    recent_messages = Message.objects.filter(
        receiver=request.user,
        receiver__branch=branch_obj
    ).order_by("-timestamp")[:5]

    data = {
        "total_animals": total_animals,
        "total_tasks": total_tasks,
        "total_medical_records": total_medical_records,
        "total_notifications": total_notifications,
        "recent_messages": [
            {
                "subject": msg.subject or "No Subject",
                "sender": msg.sender.get_full_name() or msg.sender.username,
                "timestamp": msg.timestamp.strftime("%b %d"),
            }
            for msg in recent_messages
        ]
    }

    return JsonResponse(data)


@login_required
def unread_message_count(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    count = Message.objects.filter(
        receiver=request.user,
        is_read=False,
        receiver__branch=branch_obj
    ).count()
    return JsonResponse({'unread_count': count})


@login_required
def notification_count_api(request):
    branch_id = request.GET.get('branch', None)
    if not branch_id:
        return JsonResponse({'notifications': 0, 'messages': 0})

    try:
        branch_obj = Branch.objects.get(id=branch_id)
    except Branch.DoesNotExist:
        return JsonResponse({'notifications': 0, 'messages': 0})

    notifications_count = Notification.objects.filter(
        user=request.user,
        user__branch=branch_obj,
        is_read=False
    ).count()
    messages_count = Message.objects.filter(
        receiver=request.user,
        receiver__branch=branch_obj,
        is_read=False
    ).count()

    return JsonResponse({'notifications': notifications_count, 'messages': messages_count})


@login_required
def messages_view(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    messages_qs = Message.objects.filter(
        receiver=request.user,
        receiver__branch=branch_obj
    ).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/messages.html', {'branch': branch_obj, 'messages': messages_qs})


@login_required
def notifications_view(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    notifications = Notification.objects.filter(
        user=request.user,
        user__branch=branch_obj
    ).order_by('-created_at')
    return render(request, 'veterinarian_dashboard/notifications.html', {'branch': branch_obj, 'notifications': notifications})


@login_required
def update_task_view(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    tasks = VetTask.objects.filter(
        assigned_to=request.user,
        branch=branch_obj
    ).order_by('-created_at')
    return render(request, 'veterinarian_dashboard/update_task.html', {'branch': branch_obj, 'tasks': tasks})


@login_required
def add_medical_record(request, branch):
    branch_obj = get_object_or_404(Branch, name__iexact=branch)

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES, branch=branch_obj, user=request.user)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.created_by = request.user
            medical_record.branch = branch_obj
            medical_record.save()
            messages.success(request, "Medical record added successfully.")
            return redirect('vet_dashboard', branch=branch)
        messages.error(request, "Please correct the errors below.")
    else:
        form = MedicalRecordForm(branch=branch_obj, user=request.user)

    return render(request, 'veterinarian_dashboard/add_medical_record.html', {'form': form, 'branch': branch_obj})


@login_required
def medical_records_list(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    records = MedicalRecord.objects.filter(
        veterinarian=request.user,
        animal__branch__name__iexact=branch
    ).order_by('-date_recorded')

    return render(
        request,
        'veterinarian_dashboard/medical_records_list.html',
        {'records': records, 'branch': branch}
    )


@login_required
def assign_task(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    form = VetTaskForm()
    form.fields['animal'].queryset = Animal.objects.filter(branch__name__iexact=branch)
    form.fields['assigned_to'].queryset = CustomUser.objects.filter(branch__name__iexact=branch, role__in=['staff', 'user'])

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
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(
        assigned_by=request.user,
        animal__branch__name__iexact=branch
    ).order_by('-created_at')

    return render(request, 'veterinarian_dashboard/task_list.html', {
        'tasks': tasks,
        'branch': branch
    })


@login_required
def vet_task_detail(request, branch, task_id):
    task = get_object_or_404(
        VetTask,
        id=task_id,
        assigned_by=request.user,
        animal__branch__name__iexact=branch
    )

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
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    query = request.GET.get('q', '')
    records = MedicalRecord.objects.filter(
        veterinarian=request.user,
        animal__branch__name__iexact=branch
    ).order_by('-date_recorded')

    if query:
        records = records.filter(diagnosis__icontains=query)

    return render(request, 'veterinarian_dashboard/search_medical_records.html', {
        'records': records,
        'branch': branch,
        'query': query
    })

@login_required
def pending_tasks(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(
        assigned_by=request.user,
        status='pending',
        animal__branch__name__iexact=branch
    ).order_by('-created_at')

    return render(request, 'veterinarian_dashboard/pending_tasks.html', {
        'tasks': tasks,
        'branch': branch
    })


@login_required
def completed_tasks(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(
        assigned_by=request.user,
        status='completed',
        animal__branch__name__iexact=branch
    ).order_by('-created_at')

    return render(request, 'veterinarian_dashboard/completed_tasks.html', {
        'tasks': tasks,
        'branch': branch
    })


@login_required
def add_patient(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    form = PatientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        patient = form.save(commit=False)
        patient.branch = branch_obj
        patient.save()
        return redirect('patient_list', branch=branch)

    return render(request, 'veterinarian_dashboard/add_patient.html', {'form': form, 'branch': branch})


@login_required
def patient_list(request, branch):
    patients = Animal.objects.filter(branch__name__iexact=branch)
    return render(request, 'veterinarian_dashboard/patient_list.html', {'patients': patients, 'branch': branch})


@login_required
def search_patients(request, branch):
    query = request.GET.get('q', '')
    patients = Animal.objects.filter(branch__name__iexact=branch)
    if query:
        patients = patients.filter(name__icontains=query)
    return render(request, 'veterinarian_dashboard/search_patients.html', {'branch': branch, 'patients': patients, 'query': query})


@login_required
def analytics_dashboard(request, branch):
    animals = Animal.objects.filter(branch__name__iexact=branch)
    tasks = VetTask.objects.filter(animal__branch__name__iexact=branch)

    return render(request, 'veterinarian_dashboard/analytics_dashboard.html', {
        'branch': branch,
        'total_patients': animals.count(),
        'active_cases': tasks.filter(status='pending').count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'completed_tasks': tasks.filter(status='completed').count(),
    })


@login_required
def performance_reports(request, branch):
    vet = request.user

    tasks = VetTask.objects.filter(
        assigned_to=vet,
        animal__branch__name__iexact=branch
    )

    completed_tasks = tasks.filter(status='completed', due_date__isnull=False)

    total_duration = timedelta()
    count = 0

    for task in completed_tasks:
        if task.completed_at:
            total_duration += (task.completed_at - task.created_at)
            count += 1

    avg_response_time = str(total_duration / count) if count else "N/A"

    context = {
        'branch': branch,
        'total_patients': Animal.objects.filter(
            branch__name__iexact=branch,
            assigned_users=vet
        ).count(),
        'tasks_completed': completed_tasks.count(),
        'tasks_pending': tasks.filter(status='pending').count(),
        'average_response_time': avg_response_time,
    }

    return render(request, 'veterinarian_dashboard/performance_reports.html', context)


@login_required
def vet_settings(request, branch):
    return render(request, 'veterinarian_dashboard/vet_settings.html', {'branch': branch})


@login_required
def help_support(request, branch):
    return render(request, 'veterinarian_dashboard/help_support.html', {'branch': branch})


@login_required
def equipment_log_view(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    form = EquipmentLogForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.user = request.user
        log.save()
        messages.success(request, "Equipment log entry added successfully.")
        return redirect('equipment_logs', branch=branch)

    logs = EquipmentLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/equipment_log.html', {
        'form': form,
        'logs': logs,
        'branch': branch
    })


@login_required
def inbox(request, branch):
    messages_qs = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    context = {'messages': messages_qs, 'branch': branch}
    return render(request, 'veterinarian_dashboard/inbox.html', context)


@login_required
def message_detail(request, branch, message_id):
    message = get_object_or_404(
        Message,
        Q(id=message_id) & (Q(receiver=request.user) | Q(sender=request.user))
    )

    if message.receiver == request.user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()

    return render(request, 'veterinarian_dashboard/message_detail.html', {
        'message': message,
        'branch': branch
    })

@login_required
def compose_message(request, branch):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            new_message = form.save(commit=False)
            new_message.sender = request.user
            new_message.branch = request.user.branch
            new_message.save()
            return redirect('inbox', branch=branch)
    else:
        form = MessageForm()
    return render(request, 'veterinarian_dashboard/messages_compose.html', {'form': form, 'branch': branch})

@login_required
def reply_message(request, branch, message_id):
    original_message = get_object_or_404(
        Message,
        id=message_id,
        branch__name__iexact=branch,
        # This ensures only participants can reply
        # Either the user is the sender or receiver
    )
    if original_message.sender != request.user and original_message.receiver != request.user:
        return redirect('inbox', branch=branch)  # Prevent unauthorized access

    if request.method == 'POST':
        form = MessageReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.receiver = original_message.sender if original_message.receiver == request.user else original_message.receiver
            reply.subject = f"Re: {original_message.subject}"
            reply.parent = original_message
            reply.branch = original_message.branch
            reply.timestamp = timezone.now()
            reply.save()
            return redirect('inbox', branch=branch)
    else:
        form = MessageReplyForm()

    return render(request, 'veterinarian_dashboard/message_reply.html', {
        'form': form,
        'original_message': original_message,
        'branch': branch
    })


@login_required
def report_emergency_view(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    form = EmergencyReportForm(request.POST or None, request.FILES or None, user=request.user)
    
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.save()
        messages.success(request, "Emergency report submitted successfully.")
        return redirect('vet_dashboard', branch=branch)

    return render(request, 'veterinarian_dashboard/report_emergency.html', {
        'form': form,
        'branch': branch,
    })


@login_required
def support_request_view(request, branch):
    if not is_authorized_branch(request.user, branch, role='veterinarian'):
        return render(request, 'errors/unauthorized.html', status=403)

    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    form = SupportTicketForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.created_by = request.user
        ticket.branch = branch_obj
        ticket.save()
        messages.success(request, "Support ticket created successfully.")
        return redirect('support_request', branch=branch)

    my_tickets = SupportTicket.objects.filter(
        created_by=request.user,
        branch=branch_obj
    ).order_by('-created_at')
    
    return render(request, 'veterinarian_dashboard/support_request.html', {
        'form': form,
        'my_tickets': my_tickets,
        'branch': branch
    })


@login_required
def send_message(request, branch):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.branch = request.user.branch
            message.save()
            return redirect('vet_dashboard', branch=branch)
    else:
        form = MessageForm()
    return render(request, 'veterinarian_dashboard/send_message.html', {'form': form, 'branch': branch})



@login_required
def sent_messages(request, branch):
    # Filter messages sent by the current user within the given branch
    messages = Message.objects.filter(sender=request.user, branch__name__iexact=branch).order_by('-timestamp')
    context = {
        'sent_messages': messages,
        'branch': branch,
    }
    return render(request, 'veterinarian_dashboard/messages/sent_messages.html', context)

@login_required
def archived_messages(request, branch):
    archived = Message.objects.filter(receiver=request.user, is_archived=True).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/archived_messages.html', {'messages': archived, 'branch': branch})


@login_required
def deleted_messages(request, branch):
    deleted = Message.objects.filter(receiver=request.user, is_deleted=True).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/deleted_messages.html', {
        'messages': deleted,
        'branch': branch,
    })

@login_required
def search_animal_logs(request, branch):
    logs = AnimalLog.objects.filter(branch__name__iexact=branch)

    query = request.GET.get('q')
    if query:
        logs = logs.filter(description__icontains=query)

    context = {
        'branch': branch,
        'logs': logs,
    }
    return render(request, 'veterinarian_dashboard/search_animal_logs.html', context)

@login_required
def animal_logs(request, branch):
    return render(request, 'veterinarian_dashboard/animal_logs.html', {'branch': branch})

from core.views import animal_list as core_animal_list

@login_required
def vet_animal_list_wrapper(request, branch):
    request.branch_slug = branch  # optional: pass via request if needed internally
    return core_animal_list(request)

