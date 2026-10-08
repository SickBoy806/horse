from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.db.models import Avg, Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.forms import inlineformset_factory
from core.models import Animal, TrainingRecord
from .forms import TrainingRecordForm
from .models import Report  # or adjust the import path as needed
from core.forms import ReportForm
from core.models import TrainingSession
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import TrainingRecord, Report





from .models import (
    Branch, Animal, Notification, Message, VetTask, 
    SupportTicket, TicketReply, MedicalRecord, AnimalLog,
    EquipmentLog, EmergencyIncident, DailyActivityReport
)
from .forms import MessageForm, MessageReplyForm, VetTaskForm, SupportTicketForm, TicketReplyForm, AnimalForm, AnimalStatusForm
from .forms import CertificationForm, HandlerAssignmentForm
from .models import AnimalStatusChange, Certification
from . import health
from .utils import log_action, create_notification, notify_users, can_access_branch, get_user_dashboard_url
from accounts.models import CustomUser


# ------------------------------
# Dashboard Redirect
# ------------------------------

@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on role"""
    return redirect(get_user_dashboard_url(request.user))


# ------------------------------
# Animal Views
# ------------------------------
# Create the inline formset
TrainingRecordFormSet = inlineformset_factory(
    Animal, TrainingRecord,
    form=TrainingRecordForm,
    extra=1,           # start with one blank training record
    can_delete=True
)

@login_required
def add_animal(request, branch=None):
    """Add a new animal with training records"""
    if request.user.role not in ['admin', 'veterinarian', 'superadmin']:
        return render(request, 'errors/unauthorized.html', status=403)

    branch = getattr(request.user, 'branch', None)  # get branch from user

    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, user=request.user)
        formset = TrainingRecordFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            animal = form.save(commit=False)
            animal.branch = branch
            if not animal.status_since:
                animal.status_since = animal.acquisition_date or timezone.localdate()
            animal.save()
            form.save_m2m()
            _record_status_change(animal, None, request.user, 'Registered')

            # Link training records to this animal
            formset.instance = animal
            formset.save()

            # Assign the creator to this animal
            animal.assigned_users.add(request.user)

            # Notify admins/superadmins
            admins = CustomUser.objects.filter(
                branch=branch,
                role__in=['admin', 'superadmin']
            )
            notify_users(
                users=admins,
                notification_type='animal_assigned',
                title='New Animal Added',
                message=f"New animal '{animal.name}' (#{animal.force_number}) added by {request.user.get_full_name()}.",
                link=f'/core/animals/{animal.id}/'
            )

            # Log the action
            log_action(
                user=request.user,
                action='create',
                message=f"Added animal #{animal.force_number} - {animal.name}"
            )

            messages.success(request, "Animal and training records added successfully.")
            return redirect(get_user_dashboard_url(request.user))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AnimalForm(user=request.user)
        formset = TrainingRecordFormSet()

    ctx = _role_base_context(request.user)
    ctx.update({
        'form': form,
        'formset': formset,
        'branch': branch.name.lower() if branch else '',
    })
    return render(request, 'core/add_animal.html', ctx)


@login_required
def animal_list(request):
    """List all animals with filtering and pagination"""
    user = request.user

    # Base queryset based on user role
    if user.role == 'superadmin':
        animals = Animal.objects.all()
    else:
        animals = Animal.objects.filter(branch=user.branch)

    # Apply filters
    branch_filter = request.GET.get('branch')
    species_filter = request.GET.get('species')
    status_filter = request.GET.get('status')
    search = request.GET.get('q')

    if branch_filter and user.role == 'superadmin':
        animals = animals.filter(branch__name=branch_filter)

    if species_filter:
        animals = animals.filter(species=species_filter)

    if status_filter == 'active':
        animals = animals.filter(status__in=Animal.ACTIVE_STATUSES)
    elif status_filter:
        animals = animals.filter(status=status_filter)

    if search:
        animals = animals.filter(
            Q(name__icontains=search) | 
            Q(force_number__icontains=search) |
            Q(species__icontains=search)
        )

    # Pagination
    paginator = Paginator(animals, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context for filters
    context = _role_base_context(user)
    context.update({
        'page_obj': page_obj,
        'search': search,
        'branch_filter': branch_filter,
        'species_filter': species_filter,
        'species_choices': Animal.SPECIES_CHOICES,
        'status_filter': status_filter,
        'status_choices': Animal.STATUS_CHOICES,
    })

    if user.role == 'superadmin':
        context['branches'] = Branch.objects.filter(is_active=True)

    return render(request, 'core/animal_list.html', context)


# ------------------------------
# Task Management Views
# ------------------------------

@login_required
def assign_vet_task(request):
    """Assign a veterinary task"""
    if request.user.role not in ['admin', 'veterinarian', 'superadmin']:
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = VetTaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.branch = request.user.branch
            task.save()

            # Notify the assigned user
            create_notification(
                user=task.assigned_to,
                notification_type='task_assigned',
                title='New Task Assigned',
                message=f'You have been assigned a new task: {task.title}',
                link=f'/dashboard/vet/{request.user.branch.name}/task/{task.id}/'
            )

            # Log the action
            log_action(
                user=request.user,
                action='assign',
                message=f"Assigned task '{task.title}' to {task.assigned_to.username}"
            )

            messages.success(request, "Task assigned successfully.")
            return redirect(get_user_dashboard_url(request.user))
    else:
        form = VetTaskForm(user=request.user)

    return render(request, 'core/assign_task.html', {'form': form})


# ------------------------------
# Support Ticket Views
# ------------------------------

@login_required
def ticket_list(request, branch):
    """List support tickets for a branch"""
    if not can_access_branch(request.user, branch):
        return HttpResponseForbidden("Unauthorized")

    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    tickets = SupportTicket.objects.filter(branch=branch_obj).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    paginator = Paginator(tickets, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'branch': branch,
        'status_filter': status_filter,
        'status_choices': SupportTicket.STATUS_CHOICES,
    }

    return render(request, 'core/ticket_list.html', context)


@login_required
def ticket_detail(request, branch, ticket_id):
    """View and reply to a support ticket"""
    if not can_access_branch(request.user, branch):
        return HttpResponseForbidden("Unauthorized")

    branch_obj = get_object_or_404(Branch, name__iexact=branch)
    ticket = get_object_or_404(SupportTicket, id=ticket_id, branch=branch_obj)
    replies = ticket.replies.all()

    if request.method == 'POST':
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = ticket
            reply.replied_by = request.user
            reply.save()

            # Update ticket status if it was open
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()

            # Notify ticket creator if reply is from someone else
            if request.user != ticket.created_by:
                create_notification(
                    user=ticket.created_by,
                    notification_type='message_received',
                    title='Support Ticket Reply',
                    message=f'New reply on your ticket: {ticket.subject}',
                    link=f'/core/{branch}/tickets/{ticket.id}/'
                )

            messages.success(request, "Reply added successfully.")
            return redirect('ticket_detail', branch=branch, ticket_id=ticket.id)
    else:
        form = TicketReplyForm()

    context = {
        'ticket': ticket,
        'replies': replies,
        'form': form,
        'branch': branch,
    }

    return render(request, 'core/ticket_detail.html', context)


@login_required
def ticket_create(request, branch):
    """Create a new support ticket"""
    if not can_access_branch(request.user, branch):
        return HttpResponseForbidden("Unauthorized")

    branch_obj = get_object_or_404(Branch, name__iexact=branch)

    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.branch = branch_obj
            ticket.save()

            # Notify admins about new ticket
            admins = CustomUser.objects.filter(
                branch=branch_obj,
                role__in=['admin', 'superadmin']
            )
            notify_users(
                users=admins,
                notification_type='system_alert',
                title='New Support Ticket',
                message=f'New support ticket created: {ticket.subject}',
                link=f'/core/{branch}/tickets/{ticket.id}/'
            )

            messages.success(request, "Support ticket created successfully.")
            return redirect('ticket_list', branch=branch)
    else:
        form = SupportTicketForm()

    return render(request, 'core/ticket_form.html', {'form': form, 'branch': branch})


# ------------------------------
# Messaging Views
# ------------------------------

@login_required
def inbox(request):
    """User's message inbox"""
    messages_qs = Message.objects.filter(
        receiver=request.user, 
        is_deleted=False
    ).order_by('-timestamp')
    
    paginator = Paginator(messages_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    ctx = _role_base_context(request.user)
    ctx['page_obj'] = page_obj
    return render(request, 'core/inbox.html', ctx)


@login_required
def message_detail(request, message_id):
    """View a specific message for any user type"""
    message = get_object_or_404(
        Message,
        Q(id=message_id) & (Q(receiver=request.user) | Q(sender=request.user)),
        is_deleted=False
    )

    # Mark as read if the current user is the receiver
    if message.receiver == request.user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()

    ctx = _role_base_context(request.user)
    ctx['message'] = message
    return render(request, 'core/message_detail.html', ctx)



@login_required
def compose_message(request):
    """Compose a new message"""
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()

            # Notify receiver
            create_notification(
                user=message.receiver,
                notification_type='message_received',
                title='New Message',
                message=f'New message from {request.user.get_full_name()}: {message.subject}',
                link=f'/core/messages/{message.id}/'
            )

            messages.success(request, "Message sent successfully.")
            return redirect('inbox')
    else:
        form = MessageForm(user=request.user)
    
    ctx = _role_base_context(request.user)
    ctx['form'] = form
    return render(request, 'core/compose_message.html', ctx)


@login_required
def reply_message(request, message_id):
    """Reply to a message"""
    original_message = get_object_or_404(
        Message, 
        id=message_id, 
        receiver=request.user,
        is_deleted=False
    )
    
    if request.method == 'POST':
        form = MessageReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.receiver = original_message.sender
            reply.parent = original_message
            reply.save()

            # Notify original sender
            create_notification(
                user=original_message.sender,
                notification_type='message_received',
                title='Message Reply',
                message=f'Reply from {request.user.get_full_name()}: {reply.subject}',
                link=f'/core/messages/{reply.id}/'
            )

            messages.success(request, "Reply sent successfully.")
            return redirect('inbox')
    else:
        initial_data = {
            'subject': f"Re: {original_message.subject}",
            'content': f"\n\n--- Original Message ---\n{original_message.content}"
        }
        form = MessageReplyForm(initial=initial_data)
    
    ctx = _role_base_context(request.user)
    ctx['form'] = form
    ctx['original_message'] = original_message
    return render(request, 'core/reply_message.html', ctx)


@login_required
def sent_messages(request, branch):
    sent_messages_qs = Message.objects.filter(
        sender=request.user,
        is_deleted=False
    ).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/messages/sent_messages.html', {'sent_messages': sent_messages_qs, 'branch': branch})


@login_required
def archived_messages(request, branch):
    messages_qs = Message.objects.filter(
        receiver=request.user,
        is_archived=True,
        is_deleted=False
    ).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/archived_messages.html', {'messages': messages_qs, 'branch': branch})


@login_required
def deleted_messages(request, branch):
    messages_qs = Message.objects.filter(
        receiver=request.user,
        is_deleted=True
    ).order_by('-timestamp')
    return render(request, 'veterinarian_dashboard/deleted_messages.html', {'messages': messages_qs, 'branch': branch})


# ------------------------------
# API Views
# ------------------------------

@login_required
def notification_count_api(request):
    """API endpoint to get unread notification count"""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def unread_message_count_api(request):
    """API endpoint to get unread message count"""
    count = request.user.received_messages.filter(
        is_read=False, 
        is_deleted=False
    ).count()
    return JsonResponse({'count': count})


@login_required
def view_animal_detail(request, animal_id, branch=None):
    if request.user.role not in ANIMAL_MANAGER_ROLES:
        return render(request, 'errors/unauthorized.html', status=403)

    animal = _get_managed_animal(request.user, animal_id)

    medical_records = animal.medical_records.all().order_by('-date_recorded')
    tasks = animal.vet_tasks.all().order_by('-due_date')      # use correct related_name
    training_records = animal.training_records.all().order_by('-date_recorded')

    log_action(
        user=request.user,
        action='view',
        message=f"Viewed animal #{animal.force_number} - {animal.name}"
    )

    context = {
        'animal': animal,
        'medical_records': medical_records,
        'tasks': tasks,
        'training_records': training_records,
        'status_form': AnimalStatusForm(instance=animal),
        'status_history': animal.status_history.select_related('changed_by')[:10],
        **_operational_record(animal),
        **_team_and_certs(animal),
        'health_items': health.schedule(Animal.objects.filter(pk=animal.pk)),
        'health_missing': [k for _, k in health.missing_records([animal])],
        'housing_now': animal.housing_assignments.filter(end_date__isnull=True).select_related('unit').first(),
        'housing_past': animal.housing_assignments.filter(end_date__isnull=False).select_related('unit')[:5],
        'hoof_visits': animal.hoof_records.all()[:3] if animal.species == 'horse' else [],
        'fitted_tack': animal.tack_items.filter(is_active=True) if animal.species == 'horse' else [],
    }

    return render(request, 'core/animal_detail.html', context)


ANIMAL_MANAGER_ROLES = ('admin', 'veterinarian', 'superadmin')


def _team_and_certs(animal):
    assignments = animal.handler_assignments.select_related('handler', 'assigned_by')
    certs = list(animal.certifications.select_related('handler').order_by('-expiry_date', '-id'))
    seen = set()
    for c in certs:  # newest per type is current; older ones were renewed
        c.superseded = c.cert_type in seen
        seen.add(c.cert_type)
    return {
        'team_current': [a for a in assignments if a.is_current],
        'team_past': [a for a in assignments if not a.is_current],
        'certifications': certs,
        'role_cert': animal.role_certificate,
        'required_cert_label': dict(Certification.TYPE_CHOICES).get(animal.required_cert_type),
        'assign_form': HandlerAssignmentForm(animal=animal, initial={'start_date': timezone.localdate()}),
        'cert_form': CertificationForm(animal=animal),
    }


def _operational_record(animal):
    """Deployment history and headline numbers for an animal's profile."""
    assignments = (animal.deployment_assignments
                   .exclude(deployment__status='cancelled')
                   .select_related('deployment', 'handler')
                   .order_by('-deployment__started_at'))
    agg = assignments.aggregate(avg=Avg('performance'))
    return {
        'recent_deployments': assignments[:5],
        'ops': {
            'deployments': assignments.count(),
            'positive': assignments.filter(deployment__outcome='positive').count(),
            'finds': animal.finds_indicated.count(),
            'avg_rating': round(agg['avg'], 1) if agg['avg'] else None,
            'last': assignments[0].deployment.started_at if assignments else None,
        },
    }


def _get_managed_animal(user, animal_id):
    """Superadmins reach every branch; everyone else only their own."""
    if user.role == 'superadmin':
        return get_object_or_404(Animal, pk=animal_id)
    return get_object_or_404(Animal, pk=animal_id, branch=user.branch)


def _record_status_change(animal, old_status, user, notes=''):
    """Audit entry for a duty-status change (old_status=None for a newly registered animal)."""
    if old_status == animal.status:
        return
    AnimalStatusChange.objects.create(
        animal=animal, old_status=old_status or '', new_status=animal.status,
        changed_by=user, notes=notes,
    )
    log_action(
        user=user, action='update',
        message=f"Status of #{animal.force_number} {animal.name}: "
                f"{old_status or 'new'} → {animal.status}",
    )


@login_required
def edit_animal(request, animal_id):
    if request.user.role not in ANIMAL_MANAGER_ROLES:
        return render(request, 'errors/unauthorized.html', status=403)

    animal = _get_managed_animal(request.user, animal_id)
    old_status, old_since = animal.status, animal.status_since

    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, instance=animal, user=request.user)
        formset = TrainingRecordFormSet(request.POST, instance=animal)
        if form.is_valid() and formset.is_valid():
            animal = form.save(commit=False)
            if animal.status != old_status and animal.status_since == old_since:
                animal.status_since = timezone.localdate()
            animal.save()
            form.save_m2m()
            formset.save()
            _record_status_change(animal, old_status, request.user, animal.status_notes)
            log_action(user=request.user, action='update',
                       message=f"Edited animal #{animal.force_number} - {animal.name}")
            messages.success(request, f"{animal.name} updated.")
            return redirect('view_animal_detail', animal_id=animal.id)
        messages.error(request, "Please correct the errors below.")
    else:
        form = AnimalForm(instance=animal, user=request.user)
        formset = TrainingRecordFormSet(instance=animal)

    ctx = _role_base_context(request.user)
    ctx.update({'form': form, 'formset': formset, 'animal': animal, 'is_edit': True})
    return render(request, 'core/add_animal.html', ctx)


@login_required
def animal_set_status(request, animal_id):
    if request.user.role not in ANIMAL_MANAGER_ROLES or request.method != 'POST':
        return redirect('view_animal_detail', animal_id=animal_id)

    animal = _get_managed_animal(request.user, animal_id)
    old_status, old_since = animal.status, animal.status_since
    form = AnimalStatusForm(request.POST, instance=animal)
    if form.is_valid():
        animal = form.save(commit=False)
        if animal.status != old_status and animal.status_since in (None, old_since):
            animal.status_since = timezone.localdate()
        animal.save()
        _record_status_change(animal, old_status, request.user, animal.status_notes)
        messages.success(request, f"{animal.name} is now {animal.get_status_display()}.")
    else:
        messages.error(request, "Could not update status — check the form.")
    return redirect('view_animal_detail', animal_id=animal.id)



def _role_base_context(user):
    from core.context_processors import role_base
    from types import SimpleNamespace
    return role_base(SimpleNamespace(user=user))


@login_required
def reports_list(request):
    """Show only the reports relevant to the logged-in user's role."""
    role = getattr(request.user, 'role', None)

    if role in ['trainer', 'worker']:
        reports = Report.objects.filter(role_category='user')
    elif role == 'veterinarian':
        reports = Report.objects.filter(role_category='veterinarian')
    elif role == 'admin':
        reports = Report.objects.filter(role_category='admin')
    elif role == 'superadmin':
        reports = Report.objects.filter(role_category='superadmin')
    else:
        reports = Report.objects.none()

    ctx = _role_base_context(request.user)
    ctx['reports'] = reports
    return render(request, 'core/reports_list.html', ctx)


@login_required
def create_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.branch = request.user.branch
            report.role_category = form.role_category_value
            report.save()
            return redirect('reports_list')
    else:
        form = ReportForm(user=request.user)

    ctx = _role_base_context(request.user)
    ctx['form'] = form
    return render(request, 'core/create_report.html', ctx)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import TrainingRecord, Report


@login_required
def training_dashboard(request):
    user = request.user
    role = getattr(user, 'role', None)

    CLEARANCE = {
        'user':         2,
        'worker':       2,
        'veterinarian': 2,
        'trainer':      2,
        'admin':        3,
        'superadmin':   3,
    }
    user_clearance = CLEARANCE.get(role, 0)

    if user_clearance == 0:
        training_records = TrainingRecord.objects.none()
        show_add_button = False

    elif role in ('worker', 'user'):
        # See only records for animals explicitly assigned to them
        training_records = (
            TrainingRecord.objects
            .filter(animal__assigned_users=user)
            .prefetch_related('sessions')
            .distinct()
        )
        show_add_button = False

    elif role == 'veterinarian':
        # See only records for animals where they are the assigned vet
        training_records = (
            TrainingRecord.objects
            .filter(animal__assigned_vet=user)
            .prefetch_related('sessions')
            .distinct()
        )
        show_add_button = True

    elif role == 'trainer':
        # See assigned animals + all animals in their branch
        training_records = (
            TrainingRecord.objects
            .filter(
                models.Q(animal__assigned_users=user) |
                models.Q(animal__branch=user.branch)
            )
            .prefetch_related('sessions')
            .distinct()
        )
        show_add_button = True

    else:
        # admin / superadmin — see everything
        training_records = (
            TrainingRecord.objects
            .all()
            .prefetch_related('sessions')
        )
        show_add_button = True

    if user_clearance >= 3:
        training_reports = Report.objects.filter(
            specific_report_type__in=[
                'training_progress',
                'training_log',
                'performance_eval',
                'behavior_assessment',
                'missed_training',
                'training_schedule',
                'special_skills',
                'daily_care',
            ]
        )
    else:
        training_reports = Report.objects.none()

    context = _role_base_context(user)
    context.update({
        'role': role,
        'user_clearance': user_clearance,
        'training_records': training_records,
        'training_reports': training_reports,
        'show_add_button': show_add_button,
    })

    return render(
        request,
        'core/universal_training_dashboard.html',
        context
    )

@login_required
def training_sessions(request):
    user = request.user
    role = getattr(user, 'role', None)

    CLEARANCE = {
        'user':         1,
        'worker':       1,
        'veterinarian': 2,
        'trainer':      2,
        'admin':        3,
        'superadmin':   3,
    }
    user_clearance = CLEARANCE.get(role, 0)

    if user_clearance == 0:
        sessions = TrainingSession.objects.none()

    elif role in ('worker', 'user'):
        sessions = (
            TrainingSession.objects
            .filter(training_record__animal__assigned_users=user)
            .select_related('training_record__animal', 'conducted_by')
            .distinct()
        )

    elif role == 'veterinarian':
        sessions = (
            TrainingSession.objects
            .filter(training_record__animal__assigned_vet=user)
            .select_related('training_record__animal', 'conducted_by')
            .distinct()
        )

    elif role == 'trainer':
        sessions = (
            TrainingSession.objects
            .filter(
                models.Q(training_record__animal__assigned_users=user) |
                models.Q(training_record__animal__branch=user.branch)
            )
            .select_related('training_record__animal', 'conducted_by')
            .distinct()
        )

    else:
        sessions = (
            TrainingSession.objects
            .all()
            .select_related('training_record__animal', 'conducted_by')
        )

    context = _role_base_context(user)
    context.update({
        'role': role,
        'user_clearance': user_clearance,
        'sessions': sessions,
    })

    return render(request, 'core/training_sessions.html', context)


@login_required
def training_progression(request):
    user = request.user
    role = getattr(user, 'role', None)

    CLEARANCE = {
        'user':         1,
        'worker':       1,
        'veterinarian': 2,
        'trainer':      2,
        'admin':        3,
        'superadmin':   3,
    }
    user_clearance = CLEARANCE.get(role, 0)

    if user_clearance == 0:
        records = TrainingRecord.objects.none()

    elif role in ('worker', 'user'):
        records = (
            TrainingRecord.objects
            .filter(animal__assigned_users=user)
            .prefetch_related('sessions')
            .distinct()
        )

    elif role == 'veterinarian':
        records = (
            TrainingRecord.objects
            .filter(animal__assigned_vet=user)
            .prefetch_related('sessions')
            .distinct()
        )

    elif role == 'trainer':
        records = (
            TrainingRecord.objects
            .filter(
                models.Q(animal__assigned_users=user) |
                models.Q(animal__branch=user.branch)
            )
            .prefetch_related('sessions')
            .distinct()
        )

    else:
        records = (
            TrainingRecord.objects
            .all()
            .prefetch_related('sessions')
        )

    context = _role_base_context(user)
    context.update({
        'role': role,
        'user_clearance': user_clearance,
        'records': records,
    })

    return render(request, 'core/training_progression.html', context)

