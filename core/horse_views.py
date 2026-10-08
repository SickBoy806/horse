"""Horse care: overview, farrier log, tack inventory, stables & kennels."""
import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.models import CustomUser
from .forms import HoofCareForm, HousingMoveForm, HousingUnitForm, TackItemForm
from .health import DUE_SOON_DAYS
from .models import Animal, Branch, HoofCareRecord, HousingAssignment, HousingUnit, TackItem
from .utils import log_action, notify_users

TACK_MANAGERS = ('admin', 'superadmin', 'staff')
HOUSING_MANAGERS = ('admin', 'superadmin', 'veterinarian', 'staff')
UNIT_MANAGERS = ('admin', 'superadmin')


def _scope(qs, user, field='branch'):
    """Superadmins see every branch; everyone else only their own."""
    return qs if user.role == 'superadmin' else qs.filter(**{field: user.branch})


def _back(request, default):
    """Redirect to a same-site ?next= URL if given, otherwise to the named default view."""
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect(default)


def _can_work(user):
    return user.role == 'superadmin' or user.branch_id is not None


def _due_state(due):
    if not due:
        return 'none'
    days = (due - timezone.localdate()).days
    return 'overdue' if days < 0 else 'due_soon' if days <= DUE_SOON_DAYS else 'upcoming'


# ------------------------------
# Overview
# ------------------------------

@login_required
def horse_care_overview(request):
    user = request.user
    horses = _scope(Animal.objects.filter(species='horse', status__in=Animal.ACTIVE_STATUSES), user)
    horses = horses.select_related('branch').prefetch_related(
        Prefetch('hoof_records', queryset=HoofCareRecord.objects.order_by('-date', '-id'), to_attr='visits'),
        Prefetch('housing_assignments', queryset=HousingAssignment.objects.filter(end_date__isnull=True)
                 .select_related('unit'), to_attr='housing_now'),
        Prefetch('tack_items', queryset=TackItem.objects.filter(is_active=True), to_attr='tack'),
    ).order_by('name')

    rows = []
    for h in horses:
        last = h.visits[0] if h.visits else None
        rows.append({
            'horse': h,
            'last_visit': last,
            'farrier_state': _due_state(last.next_due) if last else 'missing',
            'unit': h.housing_now[0].unit if h.housing_now else None,
            'tack_count': len(h.tack),
            'tack_issues': sum(1 for t in h.tack if t.needs_attention),
        })

    tack = _scope(TackItem.objects.filter(is_active=True), user)
    return render(request, 'core/horse_care/overview.html', {
        'tab': 'overview', 'rows': rows,
        'stats': {
            'horses': len(rows),
            'farrier_overdue': sum(1 for r in rows if r['farrier_state'] in ('overdue', 'missing')),
            'farrier_due_soon': sum(1 for r in rows if r['farrier_state'] == 'due_soon'),
            'tack_attention': sum(1 for t in tack if t.needs_attention),
            'unhoused': sum(1 for r in rows if not r['unit']),
        },
    })


# ------------------------------
# Farrier log
# ------------------------------

@login_required
def farrier_log(request):
    user = request.user
    branch = None if user.role == 'superadmin' else user.branch

    if request.method == 'POST':
        if not _can_work(user):
            return render(request, 'errors/unauthorized.html', status=403)
        form = HoofCareForm(request.POST, branch=branch)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.recorded_by = user
            if not visit.next_due and visit.service != 'inspection':
                visit.next_due = visit.date + timedelta(days=HoofCareRecord.DEFAULT_INTERVAL_DAYS)
            visit.save()
            log_action(user=user, action='create',
                       message=f"Farrier: {visit.get_service_display()} for #{visit.animal.force_number}")
            if visit.condition in ('poor', 'lame'):
                vets = CustomUser.objects.filter(branch=visit.animal.branch, role='veterinarian', is_active=True)
                notify_users(users=vets, notification_type='system_alert',
                             title=f'Hoof problem: {visit.animal.name}',
                             message=f"Farrier reported hoof condition '{visit.get_condition_display()}' "
                                     f"for {visit.animal.name}. {visit.notes[:120]}",
                             link=f'/core/animals/{visit.animal.id}/')
            messages.success(request, f"Farrier visit for {visit.animal.name} recorded"
                                      + (f" — next due {visit.next_due:%d %b %Y}." if visit.next_due else "."))
            return redirect('farrier_log')
        messages.error(request, 'Please correct the errors in the farrier form.')
    else:
        initial = {'animal': request.GET['animal']} if request.GET.get('animal', '').isdigit() else {}
        form = HoofCareForm(branch=branch, initial=initial)

    records = _scope(HoofCareRecord.objects.select_related('animal', 'recorded_by'), user, 'animal__branch')
    horse_filter = request.GET.get('horse', '')
    if horse_filter.isdigit():
        records = records.filter(animal_id=int(horse_filter))
    return render(request, 'core/horse_care/farrier.html', {
        'tab': 'farrier', 'form': form, 'records': records[:100], 'horse_filter': horse_filter,
        'horses': _scope(Animal.objects.filter(species='horse'), user).order_by('name'),
        'can_log': _can_work(user), 'default_weeks': HoofCareRecord.DEFAULT_INTERVAL_DAYS // 7,
    })


# ------------------------------
# Tack inventory
# ------------------------------

@login_required
def tack_list(request):
    user = request.user
    items = _scope(TackItem.objects.select_related('assigned_horse', 'branch'), user)
    f = {k: request.GET.get(k, '') for k in ('type', 'condition', 'horse', 'show')}
    if f['show'] != 'all':
        items = items.filter(is_active=True)
    if f['type']:
        items = items.filter(item_type=f['type'])
    if f['condition']:
        items = items.filter(condition=f['condition'])
    if f['horse'] == 'none':
        items = items.filter(assigned_horse__isnull=True)
    elif f['horse'].isdigit():
        items = items.filter(assigned_horse_id=int(f['horse']))
    items = list(items)
    if f['show'] == 'attention':
        items = [t for t in items if t.needs_attention]

    if request.GET.get('export') == 'csv':
        return _tack_csv(items)

    return render(request, 'core/horse_care/tack.html', {
        'tab': 'tack', 'items': items, 'f': f,
        'type_choices': TackItem.TYPE_CHOICES, 'condition_choices': TackItem.CONDITION_CHOICES,
        'horses': _scope(Animal.objects.filter(species='horse'), user).order_by('name'),
        'can_manage': user.role in TACK_MANAGERS, 'can_inspect': _can_work(user),
        'attention_count': sum(1 for t in _scope(TackItem.objects.filter(is_active=True), user) if t.needs_attention),
        'interval': TackItem.INSPECTION_INTERVAL_DAYS,
    })


def _tack_csv(items):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="tack-inventory-{timezone.localdate():%Y%m%d}.csv"'
    response.write('﻿')
    w = csv.writer(response)
    w.writerow(['Type', 'Asset tag', 'Description', 'Size', 'Branch', 'Assigned horse', 'Condition',
                'Last inspected', 'Next inspection', 'In service', 'Notes'])
    for t in items:
        w.writerow([t.get_item_type_display(), t.asset_tag, t.description, t.size, t.branch.name,
                    t.assigned_horse.name if t.assigned_horse else '', t.get_condition_display(),
                    f'{t.last_inspected:%Y-%m-%d}' if t.last_inspected else '',
                    f'{t.next_inspection:%Y-%m-%d}' if t.next_inspection else 'Overdue',
                    'Yes' if t.is_active else 'No', t.notes])
    return response


@login_required
def tack_edit(request, item_id=None):
    user = request.user
    if user.role not in TACK_MANAGERS:
        return render(request, 'errors/unauthorized.html', status=403)
    item = get_object_or_404(_scope(TackItem.objects.all(), user), pk=item_id) if item_id else \
        TackItem(branch=user.branch)
    if request.method == 'POST':
        form = TackItemForm(request.POST, instance=item, user=user)
        if form.is_valid():
            item = form.save()
            log_action(user=user, action='update' if item_id else 'create',
                       message=f"Tack {'updated' if item_id else 'added'}: {item}")
            messages.success(request, f"{item} saved.")
            return redirect('tack_list')
    else:
        initial = {'assigned_horse': request.GET['horse']} if request.GET.get('horse', '').isdigit() else {}
        form = TackItemForm(instance=item, user=user, initial=initial)
    return render(request, 'core/horse_care/tack_form.html', {'tab': 'tack', 'form': form, 'item': item,
                                                               'is_new': item_id is None})


@login_required
def tack_inspect(request, item_id):
    """Quick 'inspected today' action with the condition found."""
    user = request.user
    item = get_object_or_404(_scope(TackItem.objects.all(), user), pk=item_id)
    if request.method == 'POST' and _can_work(user):
        condition = request.POST.get('condition') or item.condition
        if condition in dict(TackItem.CONDITION_CHOICES):
            item.condition = condition
            item.last_inspected = timezone.localdate()
            item.save(update_fields=['condition', 'last_inspected', 'updated_at'])
            log_action(user=user, action='update', message=f"Tack inspected: {item} ({item.get_condition_display()})")
            messages.success(request, f"{item} inspected — {item.get_condition_display().lower()}.")
    return _back(request, 'tack_list')


# ------------------------------
# Stables & kennels
# ------------------------------

@login_required
def stables_board(request):
    user = request.user
    branch_filter = request.GET.get('branch', '') if user.role == 'superadmin' else ''
    units = _scope(HousingUnit.objects.filter(is_active=True), user).select_related('branch')
    animals = _scope(Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES), user)
    if branch_filter:
        units, animals = units.filter(branch__name=branch_filter), animals.filter(branch__name=branch_filter)

    units = units.prefetch_related(Prefetch(
        'assignments', queryset=HousingAssignment.objects.filter(end_date__isnull=True).select_related('animal'),
        to_attr='current'))
    groups = {}
    for u in units.order_by('kind', 'name'):
        groups.setdefault(u.get_kind_display(), []).append(u)
    housed_ids = HousingAssignment.objects.filter(end_date__isnull=True).values_list('animal_id', flat=True)
    unhoused = animals.exclude(id__in=housed_ids).order_by('species', 'name')

    move_branch = None if user.role == 'superadmin' else user.branch
    return render(request, 'core/horse_care/stables.html', {
        'tab': 'stables', 'groups': groups, 'unhoused': unhoused,
        'move_form': HousingMoveForm(branch=move_branch, initial=_move_initial(request)),
        'unit_form': HousingUnitForm(),
        'can_move': user.role in HOUSING_MANAGERS, 'can_manage_units': user.role in UNIT_MANAGERS,
        'branches': Branch.objects.filter(is_active=True).order_by('name') if user.role == 'superadmin' else None,
        'branch_filter': branch_filter,
        'totals': {'units': sum(len(g) for g in groups.values()),
                   'capacity': sum(u.capacity for g in groups.values() for u in g),
                   'occupied': sum(len(u.current) for g in groups.values() for u in g)},
    })


def _move_initial(request):
    return {k: request.GET[k] for k in ('animal', 'unit') if request.GET.get(k, '').isdigit()}


@login_required
def housing_move(request):
    user = request.user
    if user.role not in HOUSING_MANAGERS or request.method != 'POST':
        return redirect('stables_board')
    form = HousingMoveForm(request.POST, branch=None if user.role == 'superadmin' else user.branch)
    if not form.is_valid():
        errors = '; '.join(' '.join(e) for e in form.errors.values())
        messages.error(request, f"Could not move animal — {errors}")
        return redirect('stables_board')

    move = form.save(commit=False)
    move.moved_by = user
    with transaction.atomic():
        for current in move.animal.housing_assignments.filter(end_date__isnull=True):
            current.end_date = max(move.start_date, current.start_date)
            current.save(update_fields=['end_date'])
        move.save()
    log_action(user=user, action='update', message=f"Moved #{move.animal.force_number} to {move.unit.name}")
    if move.unit.kind == 'isolation':
        vets = CustomUser.objects.filter(branch=move.unit.branch, role='veterinarian', is_active=True)
        notify_users(users=vets, notification_type='system_alert', title=f'{move.animal.name} moved to isolation',
                     message=f"{move.animal.name} is now in {move.unit.name}. {move.notes}".strip(),
                     link=f'/core/animals/{move.animal.id}/')
    messages.success(request, f"{move.animal.name} moved to {move.unit.name}.")
    return _back(request, 'stables_board')


@login_required
def housing_vacate(request, assignment_id):
    user = request.user
    assignment = get_object_or_404(HousingAssignment.objects.select_related('animal', 'unit'), pk=assignment_id)
    if user.role != 'superadmin' and assignment.unit.branch_id != user.branch_id:
        return render(request, 'errors/unauthorized.html', status=403)
    if user.role in HOUSING_MANAGERS and request.method == 'POST' and assignment.end_date is None:
        assignment.end_date = timezone.localdate()
        assignment.save(update_fields=['end_date'])
        log_action(user=user, action='update', message=f"Removed #{assignment.animal.force_number} from {assignment.unit.name}")
        messages.success(request, f"{assignment.animal.name} removed from {assignment.unit.name}.")
    return redirect('stables_board')


@login_required
def housing_unit_save(request, unit_id=None):
    user = request.user
    if user.role not in UNIT_MANAGERS or request.method != 'POST':
        return redirect('stables_board')
    if unit_id:
        unit = get_object_or_404(_scope(HousingUnit.objects.all(), user), pk=unit_id)
        branch = unit.branch
    else:
        branch = user.branch
        if user.role == 'superadmin':
            branch = Branch.objects.filter(pk=request.POST.get('branch')).first() or user.branch
        unit = HousingUnit(branch=branch)
    form = HousingUnitForm(request.POST, instance=unit, branch=branch)
    if form.is_valid():
        if unit_id and not form.cleaned_data['is_active'] and unit.assignments.filter(end_date__isnull=True).exists():
            messages.error(request, f"{unit.name} still has animals in it — move them first.")
            return redirect('stables_board')
        occupied = unit.assignments.filter(end_date__isnull=True).count() if unit_id else 0
        if form.cleaned_data['capacity'] < occupied:
            messages.error(request, f"{unit.name} has {occupied} animals — capacity can't be lower.")
            return redirect('stables_board')
        unit = form.save()
        log_action(user=user, action='update' if unit_id else 'create', message=f"Housing unit saved: {unit.name}")
        messages.success(request, f"{unit.name} saved.")
    else:
        errors = '; '.join(' '.join(e) for e in form.errors.values())
        messages.error(request, f"Could not save unit — {errors}")
    return redirect('stables_board')
