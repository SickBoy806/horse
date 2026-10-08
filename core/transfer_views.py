"""Branch-to-branch animal transfers: request -> approve/reject -> receive."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomUser
from .forms import TransferRequestForm
from .models import Animal, AnimalTransfer, HandlerAssignment, HousingAssignment, TackItem
from .utils import log_action, notify_users

REQUESTER_ROLES = ('admin', 'veterinarian', 'superadmin')


def _is_admin_of(user, branch):
    return user.role == 'superadmin' or (user.role == 'admin' and user.branch_id == branch.id)


def can_decide(user, transfer):
    return transfer.status == 'pending' and _is_admin_of(user, transfer.to_branch)


def can_receive(user, transfer):
    return transfer.status == 'approved' and _is_admin_of(user, transfer.to_branch)


def can_cancel(user, transfer):
    return transfer.status in AnimalTransfer.OPEN_STATUSES and (
        user.role == 'superadmin' or transfer.requested_by_id == user.id
        or (user.role == 'admin' and user.branch_id == transfer.from_branch_id))


def _notify(transfer, title, message, extra_users=()):
    branches = (transfer.from_branch, transfer.to_branch)
    users = set(CustomUser.objects.filter(branch__in=branches, role='admin', is_active=True))
    users |= set(CustomUser.objects.filter(role='superadmin', is_active=True))
    users |= set(u for u in extra_users if u)
    notify_users(users=users, notification_type='system_alert', title=title, message=message,
                 link='/core/transfers/')


@login_required
def transfer_list(request):
    user = request.user
    transfers = AnimalTransfer.objects.select_related('animal', 'from_branch', 'to_branch', 'requested_by', 'decided_by')
    if user.role != 'superadmin':
        transfers = transfers.filter(Q(from_branch=user.branch) | Q(to_branch=user.branch))
    view = request.GET.get('view', 'open')
    if view == 'open':
        transfers = transfers.filter(status__in=AnimalTransfer.OPEN_STATUSES)
    elif view == 'incoming' and user.branch_id:
        transfers = transfers.filter(to_branch=user.branch)
    elif view == 'outgoing' and user.branch_id:
        transfers = transfers.filter(from_branch=user.branch)

    rows = [{'t': t, 'decide': can_decide(user, t), 'receive': can_receive(user, t), 'cancel': can_cancel(user, t)}
            for t in transfers[:200]]
    return render(request, 'core/transfers/list.html', {'rows': rows, 'view': view})


@login_required
def transfer_request(request, animal_id):
    user = request.user
    if user.role not in REQUESTER_ROLES:
        return render(request, 'errors/unauthorized.html', status=403)
    animal = get_object_or_404(Animal if user.role == 'superadmin' else Animal.objects.filter(branch=user.branch),
                               pk=animal_id)
    if request.method == 'POST':
        form = TransferRequestForm(request.POST, animal=animal)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.animal, transfer.from_branch, transfer.requested_by = animal, animal.branch, user
            transfer.save()
            log_action(user=user, action='create',
                       message=f"Requested transfer of #{animal.force_number} to {transfer.to_branch.name}")
            _notify(transfer, 'Transfer requested',
                    f"{animal.name} ({animal.force_number}): {transfer.from_branch.name} -> {transfer.to_branch.name}. "
                    f"Awaiting approval.")
            messages.success(request, f"Transfer of {animal.name} to {transfer.to_branch.name} requested.")
            return redirect('view_animal_detail', animal_id=animal.id)
    else:
        form = TransferRequestForm(animal=animal)
    return render(request, 'core/transfers/request.html', {'form': form, 'animal': animal})


@login_required
def transfer_action(request, transfer_id):
    """approve / reject / receive / cancel — all POST, each with its own permission."""
    user = request.user
    transfer = get_object_or_404(AnimalTransfer.objects.select_related('animal', 'from_branch', 'to_branch'),
                                 pk=transfer_id)
    action = request.POST.get('action')
    notes = (request.POST.get('notes') or '').strip()[:255]
    animal = transfer.animal
    if request.method != 'POST':
        return redirect('transfer_list')

    done = True
    if action in ('approve', 'reject') and can_decide(user, transfer):
        transfer.status = 'approved' if action == 'approve' else 'rejected'
        transfer.decided_by, transfer.decided_at, transfer.decision_notes = user, timezone.now(), notes
        transfer.save()
        _notify(transfer, f"Transfer {transfer.status}",
                f"{animal.name}: {transfer.from_branch.name} -> {transfer.to_branch.name} {transfer.status}"
                + (f" — {notes}" if notes else '.'), extra_users=[transfer.requested_by])
        messages.success(request, f"Transfer {transfer.status}.")
    elif action == 'receive' and can_receive(user, transfer):
        with transaction.atomic():
            _complete(transfer, user)
        _notify(transfer, 'Transfer completed',
                f"{animal.name} has arrived at {transfer.to_branch.name}.", extra_users=[transfer.requested_by])
        messages.success(request, f"{animal.name} received at {transfer.to_branch.name}. Assign a handler and housing.")
        log_action(user=user, action='update', message=f"Transfer #{transfer.id} receive ({animal.force_number})")
        return redirect('view_animal_detail', animal_id=animal.id)
    elif action == 'cancel' and can_cancel(user, transfer):
        transfer.status = 'cancelled'
        transfer.decision_notes = notes or transfer.decision_notes
        transfer.save()
        _notify(transfer, 'Transfer cancelled', f"Transfer of {animal.name} was cancelled.")
        messages.success(request, 'Transfer cancelled.')
    else:
        done = False
        messages.error(request, 'That action is not available to you for this transfer.')
    if done:
        log_action(user=user, action='update', message=f"Transfer #{transfer.id} {action} ({animal.force_number})")
    if request.POST.get('back') == 'animal':
        return redirect('view_animal_detail', animal_id=animal.id)
    return redirect('transfer_list')


def _complete(transfer, user):
    """Move the animal and release everything tied to the old branch."""
    animal, today = transfer.animal, timezone.localdate()
    old_handlers = [a.handler for a in animal.handler_assignments.filter(end_date__isnull=True).select_related('handler')]
    HandlerAssignment.objects.filter(animal=animal, end_date__isnull=True).update(end_date=today)
    HousingAssignment.objects.filter(animal=animal, end_date__isnull=True).update(end_date=today)
    TackItem.objects.filter(assigned_horse=animal).update(assigned_horse=None)
    animal.assigned_users.clear()
    animal.branch = transfer.to_branch
    animal.assigned_vet = None
    animal.save(update_fields=['branch', 'assigned_vet', 'updated_at'])
    transfer.status, transfer.received_by, transfer.received_at = 'completed', user, timezone.now()
    transfer.save()
    if old_handlers:
        notify_users(users=old_handlers, notification_type='animal_assigned', title='Animal transferred',
                     message=f"{animal.name} has been transferred to {transfer.to_branch.name}; your assignment has ended.",
                     link='/core/transfers/')
