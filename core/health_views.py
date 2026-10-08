import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .health import DUE_SOON_DAYS, KINDS, missing_records, schedule, scoped_animals
from .models import Branch


@login_required
def health_schedule(request):
    user = request.user
    animals = scoped_animals(user)
    branch_filter = request.GET.get('branch', '') if user.role == 'superadmin' else ''
    if branch_filter:
        animals = animals.filter(branch__name=branch_filter)

    items = schedule(animals)
    missing = missing_records(list(animals))
    counts = {s: sum(1 for i in items if i.state == s) for s in ('overdue', 'due_soon', 'upcoming')}
    counts['missing'] = len(missing)

    state = request.GET.get('state', '')
    kind = request.GET.get('kind', '')
    if kind in KINDS:
        items = [i for i in items if i.kind == kind]
        missing = [m for m in missing if m[1] == kind]
    if state in ('overdue', 'due_soon', 'upcoming'):
        items = [i for i in items if i.state == state]
    if state and state != 'missing':
        missing = []
    if state == 'missing':
        items = []

    if request.GET.get('export') == 'csv':
        return _csv(items, missing)

    return render(request, 'core/health/schedule.html', {
        'items': items, 'missing': missing, 'counts': counts, 'state': state, 'kind': kind,
        'kinds': KINDS.items(), 'branch_filter': branch_filter, 'due_soon_days': DUE_SOON_DAYS,
        'branches': Branch.objects.filter(is_active=True).order_by('name') if user.role == 'superadmin' else None,
        'can_record': user.role == 'veterinarian' and user.branch is not None,
        'can_log_farrier': user.branch is not None or user.role == 'superadmin',
    })


def _csv(items, missing):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="health-schedule-{timezone.localdate():%Y%m%d}.csv"'
    response.write('﻿')
    w = csv.writer(response)
    w.writerow(['Animal', 'Force No.', 'Branch', 'Type', 'Product', 'Last given', 'Due', 'Days', 'State', 'By (vet / farrier)'])
    for i in items:
        w.writerow([i.animal.name, i.animal.force_number, i.animal.branch.name, i.kind_label, i.label,
                    f'{i.last_given:%Y-%m-%d}', f'{i.due_date:%Y-%m-%d}', i.days, i.state_label, i.by])
    for animal, kind in missing:
        w.writerow([animal.name, animal.force_number, animal.branch.name, KINDS[kind], '', '', '', '',
                    'No record', ''])
    return response
