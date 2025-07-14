from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from core.models import Branch

from .forms import TaskForm
from .models import Task
from core.models import Animal, Notification
from core.forms import AnimalForm
from core.utils import log_action
from accounts.models import CustomUser
from .models import SupportTicket, TicketReply  # assuming these are in support app
from .forms import SupportTicketForm, TicketReplyForm  # adjust as needed

# ------------------------------
# Task Assignment View
# ------------------------------

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
            return redirect('dashboard_home')  # adjust route if needed
    else:
        form = TaskForm(user=request.user)

    return render(request, 'tasks/assign_task.html', {'form': form})


# ------------------------------
# Ticket Views
# ------------------------------

@login_required
def ticket_list(request, branch):
    if request.user.branch != branch:
        return HttpResponseForbidden("Unauthorized")

    tickets = SupportTicket.objects.filter(branch=branch).order_by('-created_at')
    return render(request, 'support/ticket_list.html', {'tickets': tickets, 'branch': branch})


@login_required
def ticket_detail(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, branch=branch)
    replies = ticket.replies.all().order_by('created_at')

    if request.user.branch != branch:
        return HttpResponseForbidden("Unauthorized")

    if request.method == 'POST':
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = ticket
            reply.replied_by = request.user
            reply.save()
            return redirect('ticket_detail', branch=branch, ticket_id=ticket.id)
    else:
        form = TicketReplyForm()

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'form': form,
        'branch': branch,
    })


@login_required
def ticket_create(request, branch):
    if request.user.branch != branch:
        return HttpResponseForbidden("Unauthorized")

    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.branch = branch
            ticket.save()
            return redirect('ticket_list', branch=branch)
    else:
        form = SupportTicketForm()

    return render(request, 'support/ticket_form.html', {'form': form, 'branch': branch})


@login_required
def ticket_close(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, branch=branch)

    if request.user.branch != branch or request.user.role not in ['admin', 'superadmin', 'veterinarian']:
        return HttpResponseForbidden("Unauthorized")

    ticket.status = 'closed'
    ticket.save()
    return redirect('ticket_detail', branch=branch, ticket_id=ticket.id)


# ------------------------------
# Animal Views
# ------------------------------


@login_required
def add_animal(request):
    if request.user.role not in ['admin', 'veterinarian']:
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            animal = form.save(commit=False)

            # ✅ FIX: get actual Branch object from branch name
            try:
                animal.branch = Branch.objects.get(name=request.user.branch)
            except Branch.DoesNotExist:
                return render(request, 'errors/branch_not_found.html', status=400)

            animal.save()
            form.save_m2m()

            # Optionally assign the user who added it
            animal.assigned_users.add(request.user)

            # Notify SuperAdmins
            superadmins = CustomUser.objects.filter(role='superadmin')
            for admin in superadmins:
                Notification.objects.create(
                    user=admin,
                    message=f"New animal '{animal.name}' (#{animal.force_number}) added by {request.user.get_full_name()}."
                )

            # Log the action
            log_action(
                user=request.user,
                action='create',
                message=f"Added animal #{animal.force_number} - {animal.name}"
            )

            messages.success(request, "Animal added successfully.")
            return redirect('add_animal')
    else:
        form = AnimalForm()

    return render(request, 'core/add_animal.html', {'form': form})

@login_required
def view_animal_detail(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)

    if request.user.role != 'superadmin' and not animal.assigned_users.filter(branch=request.user.branch).exists():
        return render(request, 'errors/unauthorized.html', status=403)

    assigned_users = animal.assigned_users.all()

    return render(request, 'core/animal_detail.html', {
        'animal': animal,
        'assigned_users': assigned_users,
    })


@login_required
def animal_list(request):
    user = request.user

    # Base queryset
    if user.role == 'superadmin':
        animals = Animal.objects.all()
    else:
        # Fix: match branch by name since user.branch is a string like 'TPS_Moshi'
        animals = Animal.objects.filter(branch__name=user.branch)

    # Filters from query params
    branch_filter = request.GET.get('branch')
    species_filter = request.GET.get('species')

    # Only superadmin can filter by branch
    if branch_filter and user.role == 'superadmin':
        animals = animals.filter(branch__name=branch_filter)

    if species_filter:
        animals = animals.filter(species__icontains=species_filter)

    # Pagination
    paginator = Paginator(animals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'branches': Animal.objects.values_list('branch__name', flat=True).distinct(),
        'species_list': Animal.objects.values_list('species', flat=True).distinct(),
        'branch_filter': branch_filter,
        'species_filter': species_filter,
    }

    return render(request, 'core/animal_list.html', context)
