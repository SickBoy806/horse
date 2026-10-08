"""Handler teams and certifications."""
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CertificationForm, HandlerAssignmentForm
from .models import Animal, Branch, Certification, HandlerAssignment
from .utils import create_notification, log_action

MANAGER_ROLES = ('admin', 'veterinarian', 'superadmin')


def _managed_animal(user, animal_id):
    if user.role == 'superadmin':
        return get_object_or_404(Animal, pk=animal_id)
    return get_object_or_404(Animal, pk=animal_id, branch=user.branch)


def _back(animal, anchor):
    return redirect(f"/core/animals/{animal.id}/#{anchor}")


def _form_errors(form):
    return '; '.join(f"{form.fields[f].label if f in form.fields else ''} {' '.join(e)}".strip()
                     for f, e in form.errors.items())


# ------------------------------
# Handler teams
# ------------------------------

@login_required
def assign_handler(request, animal_id):
    if request.user.role not in MANAGER_ROLES or request.method != 'POST':
        return redirect('view_animal_detail', animal_id=animal_id)
    animal = _managed_animal(request.user, animal_id)
    form = HandlerAssignmentForm(request.POST, animal=animal)
    if not form.is_valid():
        messages.error(request, f"Could not assign handler — {_form_errors(form)}")
        return _back(animal, 'team')

    assignment = form.save(commit=False)
    assignment.animal = animal
    assignment.assigned_by = request.user
    if assignment.role == 'primary':
        # Handover: the outgoing primary (and the new primary's own secondary slot, on promotion)
        # end when the new assignment starts.
        for old in animal.handler_assignments.filter(end_date__isnull=True).filter(
                models.Q(role='primary') | models.Q(handler=assignment.handler)):
            _end(old, assignment.start_date, request.user)
    assignment.save()
    animal.assigned_users.add(assignment.handler)

    create_notification(
        user=assignment.handler, notification_type='animal_assigned',
        title='Handler assignment',
        message=f"You are now {assignment.get_role_display().lower()} of {animal.name} ({animal.force_number}).",
        link=f'/core/animals/{animal.id}/',
    )
    log_action(user=request.user, action='assign',
               message=f"Assigned {assignment.handler.username} as {assignment.role} handler of #{animal.force_number}")
    messages.success(request, f"{assignment.handler.get_full_name() or assignment.handler.username} "
                              f"is now {assignment.get_role_display().lower()} of {animal.name}.")
    return _back(animal, 'team')


def _end(assignment, end_date, user):
    assignment.end_date = max(end_date, assignment.start_date)
    assignment.save(update_fields=['end_date'])
    still_on_team = assignment.animal.handler_assignments.filter(
        handler=assignment.handler, end_date__isnull=True).exists()
    if not still_on_team:
        assignment.animal.assigned_users.remove(assignment.handler)
    log_action(user=user, action='update',
               message=f"Ended {assignment.handler.username}'s {assignment.role} handler assignment "
                       f"for #{assignment.animal.force_number}")


@login_required
def end_assignment(request, assignment_id):
    assignment = get_object_or_404(HandlerAssignment.objects.select_related('animal', 'handler'), pk=assignment_id)
    animal = _managed_animal(request.user, assignment.animal_id)  # enforces branch scope
    if request.user.role in MANAGER_ROLES and request.method == 'POST' and assignment.is_current:
        _end(assignment, timezone.localdate(), request.user)
        messages.success(request, f"Ended {assignment.handler.get_full_name() or assignment.handler.username}'s "
                                  f"assignment to {animal.name}.")
    return _back(animal, 'team')


# ------------------------------
# Certifications
# ------------------------------

@login_required
def add_certification(request, animal_id):
    if request.user.role not in MANAGER_ROLES or request.method != 'POST':
        return redirect('view_animal_detail', animal_id=animal_id)
    animal = _managed_animal(request.user, animal_id)
    form = CertificationForm(request.POST, request.FILES, animal=animal)
    if not form.is_valid():
        messages.error(request, f"Could not record certificate — {_form_errors(form)}")
        return _back(animal, 'certifications')
    cert = form.save(commit=False)
    cert.animal = animal
    cert.recorded_by = request.user
    cert.save()
    log_action(user=request.user, action='create',
               message=f"Recorded {cert.get_cert_type_display()} certificate for #{animal.force_number}, "
                       f"expires {cert.expiry_date:%Y-%m-%d}")
    messages.success(request, f"{cert.get_cert_type_display()} certificate recorded "
                              f"(valid to {cert.expiry_date:%d %b %Y}).")
    return _back(animal, 'certifications')


@login_required
def delete_certification(request, cert_id):
    cert = get_object_or_404(Certification.objects.select_related('animal'), pk=cert_id)
    animal = _managed_animal(request.user, cert.animal_id)
    if request.user.role in ('admin', 'superadmin') and request.method == 'POST':
        log_action(user=request.user, action='delete',
                   message=f"Deleted {cert.get_cert_type_display()} certificate #{cert.id} for #{animal.force_number}")
        cert.delete()
        messages.success(request, 'Certificate removed.')
    return _back(animal, 'certifications')


# ------------------------------
# Teams & certifications roster
# ------------------------------

def roster_rows(user, branch_name=''):
    """One row per active animal: current team + the certificate its specialisation requires."""
    animals = Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES).select_related('branch')
    if user.role != 'superadmin':
        animals = animals.filter(branch=user.branch)
    elif branch_name:
        animals = animals.filter(branch__name=branch_name)
    animals = animals.prefetch_related(
        Prefetch('handler_assignments',
                 queryset=HandlerAssignment.objects.filter(end_date__isnull=True).select_related('handler'),
                 to_attr='team'),
        Prefetch('certifications', queryset=Certification.objects.order_by('-expiry_date', '-id'), to_attr='certs'),
    ).order_by('name')

    rows = []
    for a in animals:
        required = a.required_cert_type
        role_cert = next((c for c in a.certs if c.cert_type == required), None) if required else None
        latest = {}
        for c in a.certs:
            latest.setdefault(c.cert_type, c)
        rows.append({
            'animal': a,
            'primary': next((t.handler for t in a.team if t.role == 'primary'), None),
            'secondary': [t.handler for t in a.team if t.role == 'secondary'],
            'required': required,
            'role_cert': role_cert,
            'cert_state': (role_cert.state if role_cert else ('missing' if required else 'n/a')),
            'other_certs': [c for t, c in latest.items() if t != required],
        })
    return rows


@login_required
def teams_roster(request):
    user = request.user
    branch_name = request.GET.get('branch', '') if user.role == 'superadmin' else ''
    state = request.GET.get('state', '')
    rows = roster_rows(user, branch_name)

    counts = {k: sum(1 for r in rows if r['cert_state'] == k) for k in ('valid', 'expiring', 'expired', 'missing')}
    counts['no_handler'] = sum(1 for r in rows if not r['primary'])
    if state == 'no_handler':
        rows = [r for r in rows if not r['primary']]
    elif state:
        rows = [r for r in rows if r['cert_state'] == state]

    if request.GET.get('export') == 'csv':
        return _roster_csv(rows)

    return render(request, 'core/teams/roster.html', {
        'rows': rows, 'counts': counts, 'state': state, 'branch_filter': branch_name,
        'branches': Branch.objects.filter(is_active=True).order_by('name') if user.role == 'superadmin' else None,
        'expiring_days': Certification.EXPIRING_DAYS,
    })


def _roster_csv(rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="k9-teams-{timezone.localdate():%Y%m%d}.csv"'
    response.write('﻿')
    w = csv.writer(response)
    w.writerow(['Animal', 'Force No.', 'Species', 'Branch', 'Status', 'Specialisation', 'Primary handler',
                'Secondary handlers', 'Required certificate', 'Certificate no.', 'Expires', 'Certificate state'])
    name = lambda u: u.get_full_name() or u.username  # noqa: E731
    for r in rows:
        a, c = r['animal'], r['role_cert']
        w.writerow([a.name, a.force_number, a.get_species_display(), a.branch.name, a.get_status_display(),
                    a.get_specialisation_display(), name(r['primary']) if r['primary'] else '',
                    '; '.join(name(u) for u in r['secondary']),
                    dict(Certification.TYPE_CHOICES).get(r['required'], ''),
                    c.certificate_number if c else '', f'{c.expiry_date:%Y-%m-%d}' if c else '',
                    r['cert_state'].replace('_', ' ').title()])
    return response
