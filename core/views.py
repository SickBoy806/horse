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

@login_required
def ticket_list(request, branch):
    if request.user.branch != branch:
        return HttpResponseForbidden("Unauthorized")

    tickets = SupportTicket.objects.filter(branch=branch).order_by('-created_at')
    return render(request, 'support/ticket_list.html', {'tickets': tickets, 'branch': branch})


# View ticket detail and replies
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

# Create new ticket
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


# Close ticket
@login_required
def ticket_close(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, branch=branch)

    if request.user.branch != branch or request.user.role not in ['admin', 'superadmin', 'veterinarian']:
        return HttpResponseForbidden("Unauthorized")

    ticket.status = 'closed'
    ticket.save()
    return redirect('ticket_detail', branch=branch, ticket_id=ticket.id)