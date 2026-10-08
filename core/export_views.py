"""Exports (Excel / print-to-PDF), animal ID cards and public card verification."""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .models import Animal, Branch
from .reports_export import REPORTS, animal_dossier
from .utils import log_action
from .xlsx import build_workbook

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
CARD_MANAGERS = ('admin', 'superadmin', 'veterinarian')


def _date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _scoped_animals(user):
    qs = Animal.objects.select_related('branch')
    return qs if user.role == 'superadmin' else qs.filter(branch=user.branch)


def _deliver(request, report, filename):
    if request.GET.get('format') == 'xlsx':
        data = build_workbook((t.name, t.headers, t.rows) for t in report.tables)
        response = HttpResponse(data, content_type=XLSX)
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response
    tables = [{'name': t.name, 'headers': t.headers, 'rows': [[_display(c) for c in row] for row in t.rows]}
              for t in report.tables]
    return render(request, 'core/exports/print_report.html', {
        'report': report, 'tables': tables, 'generated_at': timezone.localtime(),
        'landscape': max((len(t.headers) for t in report.tables), default=0) > 8,  # wide tables need A4 landscape
    })


def _display(value):
    """Human formatting for the print view (Excel keeps raw values)."""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime('%d %b %Y %H:%M') if timezone.is_aware(value) else value.strftime('%d %b %Y %H:%M')
    if isinstance(value, date):
        return value.strftime('%d %b %Y')
    if isinstance(value, Decimal):
        return f'{value.normalize():f}'
    return value


@login_required
def exports_hub(request):
    user = request.user
    today = timezone.localdate()
    return render(request, 'core/exports/hub.html', {
        'reports': [(key, title, desc, dated) for key, (title, desc, _, dated) in REPORTS.items()],
        'default_from': (today - timedelta(days=30)).isoformat(), 'default_to': today.isoformat(),
        'branches': Branch.objects.filter(is_active=True).order_by('name') if user.role == 'superadmin' else None,
        'can_cards': user.role in CARD_MANAGERS,
    })


@login_required
def export_run(request, key):
    if key not in REPORTS:
        return redirect('exports_hub')
    user = request.user
    title, _, builder, dated = REPORTS[key]
    branch = request.GET.get('branch', '') if user.role == 'superadmin' else ''
    date_from, date_to = (_date(request.GET.get('date_from')), _date(request.GET.get('date_to'))) if dated else (None, None)
    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from
    report = builder(user, branch_name=branch, date_from=date_from, date_to=date_to)
    log_action(user=user, action='other', message=f"Exported report: {title} ({request.GET.get('format', 'print')})")
    stamp = timezone.localdate().strftime('%Y%m%d')
    return _deliver(request, report, f"tpf-{key}-{slugify(branch) or 'scope'}-{stamp}")


@login_required
def animal_dossier_export(request, animal_id):
    animal = get_object_or_404(_scoped_animals(request.user), pk=animal_id)
    return _deliver(request, animal_dossier(animal), f"tpf-dossier-{slugify(animal.force_number)}")


# ------------------------------------------------------------------ ID cards

def _card_context(request, animals):
    cards = []
    for a in animals:
        cards.append({
            'animal': a,
            'handler': a.primary_handler,
            'cert': a.role_certificate,
            'verify_url': request.build_absolute_uri(reverse('verify_animal', args=[a.card_token])),
            'serial': str(a.card_token).split('-')[0].upper(),
        })
    return {'cards': cards}


@login_required
def animal_card(request, animal_id):
    animal = get_object_or_404(_scoped_animals(request.user), pk=animal_id)
    return render(request, 'core/exports/cards.html', {**_card_context(request, [animal]), 'single': animal,
                                                      'can_reissue': request.user.role in CARD_MANAGERS})


@login_required
def animal_cards_batch(request):
    """Printable sheet of ID cards: selected ids, or every active animal in scope."""
    animals = _scoped_animals(request.user).filter(status__in=Animal.ACTIVE_STATUSES)
    ids = [int(i) for i in request.GET.get('ids', '').split(',') if i.isdigit()]
    if ids:
        animals = animals.filter(pk__in=ids)
    if request.user.role == 'superadmin' and request.GET.get('branch'):
        animals = animals.filter(branch__name=request.GET['branch'])
    return render(request, 'core/exports/cards.html', _card_context(request, animals.order_by('branch__name', 'name')))


@login_required
def card_reissue(request, animal_id):
    """New QR token (old printed cards stop verifying) and a fresh issue date."""
    animal = get_object_or_404(_scoped_animals(request.user), pk=animal_id)
    if request.method == 'POST' and request.user.role in CARD_MANAGERS:
        animal.card_token = uuid.uuid4()
        animal.card_issued = timezone.localdate()
        animal.save(update_fields=['card_token', 'card_issued'])
        log_action(user=request.user, action='update', message=f"Reissued ID card for #{animal.force_number}")
        messages.success(request, 'New card issued — previously printed cards no longer verify.')
    return redirect('animal_card', animal_id=animal.id)


def verify_animal(request, token):
    """Public page behind the card QR code: confirms the card is genuine with minimal, non-sensitive details."""
    animal = Animal.objects.select_related('branch').filter(card_token=token).first()
    return render(request, 'core/exports/verify.html', {
        'animal': animal,
        'active': bool(animal and animal.status in Animal.ACTIVE_STATUSES),
        'checked_at': timezone.localtime(),
    }, status=200 if animal else 404)
