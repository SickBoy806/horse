"""Report definitions shared by the Excel export and the print/PDF view.

Each builder returns a Report: title, subtitle, headline figures and one or more tables. The same
object renders to a multi-sheet .xlsx or a printable A4 page, so both outputs always match.
"""
from dataclasses import dataclass, field

from django.db.models import Count, Q, Sum

from . import health
from .models import (Animal, Branch, Certification, Deployment, DeploymentFind, HandlerAssignment, MedicalRecord,
                     StockItem, StockMovement)
from .team_views import roster_rows


@dataclass
class Table:
    name: str
    headers: list
    rows: list


@dataclass
class Report:
    title: str
    subtitle: str = ''
    summary: list = field(default_factory=list)   # [(label, value)]
    tables: list = field(default_factory=list)


def _name(user):
    return (user.get_full_name() or user.username) if user else ''


def _branches(user, branch_name=''):
    qs = Branch.objects.filter(is_active=True)
    if user.role != 'superadmin':
        return qs.filter(pk=user.branch_id)
    return qs.filter(name=branch_name) if branch_name else qs


def _scope_label(user, branch_name):
    if user.role != 'superadmin':
        return user.branch.name.title() if user.branch else ''
    return branch_name.title() if branch_name else 'All branches'


# ------------------------------------------------------------------ Animal register
def animal_register(user, branch_name='', **_):
    animals = Animal.objects.filter(branch__in=_branches(user, branch_name)).select_related('branch', 'sire', 'dam')
    rows = []
    for a in animals.order_by('branch__name', 'species', 'name'):
        cert = a.role_certificate
        rows.append([a.force_number, a.name, a.branch.name, a.get_species_display(), a.breed or '', a.get_sex_display(),
                     a.date_of_birth, a.get_status_display(), a.get_specialisation_display(),
                     _name(a.primary_handler), a.microchip_number or '', a.brand_or_tattoo,
                     (f"{cert.get_cert_type_display()} - {cert.state_label} ({cert.expiry_date:%Y-%m-%d})" if cert
                      else ('Not certified' if a.required_cert_type else 'n/a')),
                     a.sire.name if a.sire else '', a.dam.name if a.dam else '', a.acquisition_date])
    by_status = dict(animals.values_list('status').annotate(n=Count('id')))
    return Report(
        title='Animal Register', subtitle=_scope_label(user, branch_name),
        summary=[('Animals', len(rows))] + [(label, by_status.get(v, 0)) for v, label in Animal.STATUS_CHOICES if by_status.get(v)],
        tables=[Table('Animals', ['Force No.', 'Name', 'Branch', 'Species', 'Breed', 'Sex', 'Date of birth', 'Status',
                                  'Specialisation', 'Primary handler', 'Microchip', 'Brand/tattoo', 'Role certificate',
                                  'Sire', 'Dam', 'Acquired'], rows)],
    )


# ------------------------------------------------------------------ Deployments
def deployments_report(user, branch_name='', date_from=None, date_to=None, **_):
    qs = Deployment.objects.filter(branch__in=_branches(user, branch_name)).exclude(status='cancelled')
    if date_from:
        qs = qs.filter(started_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(started_at__date__lte=date_to)
    qs = qs.select_related('branch').prefetch_related('team__animal', 'team__handler', 'finds').order_by('started_at')

    detail, finds_rows = [], []
    for d in qs:
        team = list(d.team.all())
        detail.append([d.reference, d.started_at, d.branch.name, d.get_deployment_type_display(), d.location,
                       d.ob_number, d.get_status_display(), d.get_outcome_display(),
                       '; '.join(t.animal.name for t in team), d.finds.count(), d.arrests, d.persons_located])
        for f in d.finds.all():
            finds_rows.append([d.reference, f.get_find_type_display(), f.description, f.quantity,
                               f.get_unit_display() if f.unit else '', f.indicated_by.name if f.indicated_by else ''])

    by_type = qs.values('deployment_type').annotate(n=Count('id'), pos=Count('id', filter=Q(outcome='positive')),
                                                   arrests=Sum('arrests')).order_by('-n')
    types = dict(Deployment.TYPE_CHOICES)
    animals = (Animal.objects.filter(deployment_assignments__deployment__in=qs)
               .annotate(n=Count('deployment_assignments', distinct=True),
                         pos=Count('deployment_assignments', filter=Q(deployment_assignments__deployment__outcome='positive'), distinct=True))
               .order_by('-pos', '-n', 'name'))
    completed = qs.filter(status='completed').exclude(outcome='').count()
    positive = qs.filter(outcome='positive').count()
    agg = qs.aggregate(arrests=Sum('arrests'), persons=Sum('persons_located'))
    return Report(
        title='Deployments & Results', subtitle=f"{_scope_label(user, branch_name)} · {_period(date_from, date_to)}",
        summary=[('Deployments', qs.count()), ('Success rate', f'{round(positive * 100 / completed)}%' if completed else '-'),
                 ('Finds', DeploymentFind.objects.filter(deployment__in=qs).count()), ('Arrests', agg['arrests'] or 0),
                 ('Persons located', agg['persons'] or 0)],
        tables=[
            Table('By type', ['Type', 'Deployments', 'Positive', 'Arrests'],
                  [[types[r['deployment_type']], r['n'], r['pos'], r['arrests'] or 0] for r in by_type]),
            Table('By animal', ['Animal', 'Force No.', 'Deployments', 'Positive'],
                  [[a.name, a.force_number, a.n, a.pos] for a in animals]),
            Table('Deployments', ['Reference', 'Started', 'Branch', 'Type', 'Location', 'OB No.', 'Status', 'Outcome',
                                  'Animals', 'Finds', 'Arrests', 'Persons located'], detail),
            Table('Finds', ['Reference', 'Type', 'Description', 'Quantity', 'Unit', 'Indicated by'], finds_rows),
        ],
    )


# ------------------------------------------------------------------ Compliance
def compliance_report(user, branch_name='', **_):
    animals = health.scoped_animals(user)
    if user.role == 'superadmin' and branch_name:
        animals = animals.filter(branch__name=branch_name)
    items = health.schedule(animals)
    missing = health.missing_records(list(animals))
    rows = roster_rows(user, branch_name)
    due = [i for i in items if i.state != 'upcoming']
    return Report(
        title='Health & Certification Compliance', subtitle=_scope_label(user, branch_name),
        summary=[('Overdue', sum(1 for i in items if i.state == 'overdue')),
                 ('Due soon', sum(1 for i in items if i.state == 'due_soon')),
                 ('Never recorded', len(missing)),
                 ('Certificates expired', sum(1 for r in rows if r['cert_state'] == 'expired')),
                 ('Not certified', sum(1 for r in rows if r['cert_state'] == 'missing')),
                 ('No handler', sum(1 for r in rows if not r['primary']))],
        tables=[
            Table('Due & overdue', ['Animal', 'Force No.', 'Branch', 'Type', 'Item', 'Last', 'Due', 'State'],
                  [[i.animal.name, i.animal.force_number, i.animal.branch.name, i.kind_label, i.label, i.last_given,
                    i.due_date, f"{i.state_label} ({i.days_late}d late)" if i.state == 'overdue' else i.state_label]
                   for i in due]),
            Table('Never recorded', ['Animal', 'Force No.', 'Branch', 'Type'],
                  [[a.name, a.force_number, a.branch.name, health.KINDS[k]] for a, k in missing]),
            Table('Teams & certificates', ['Animal', 'Force No.', 'Branch', 'Specialisation', 'Primary handler',
                                           'Required certificate', 'Expires', 'State'],
                  [[r['animal'].name, r['animal'].force_number, r['animal'].branch.name,
                    r['animal'].get_specialisation_display(), _name(r['primary']),
                    dict(Certification.TYPE_CHOICES).get(r['required'], 'n/a'),
                    r['role_cert'].expiry_date if r['role_cert'] else '',
                    r['cert_state'].replace('_', ' ').title()] for r in rows]),
        ],
    )


# ------------------------------------------------------------------ Stores
def stores_report(user, branch_name='', date_from=None, date_to=None, **_):
    from .stock_views import with_on_hand  # local import: stock_views imports forms

    items = list(with_on_hand(StockItem.objects.filter(branch__in=_branches(user, branch_name), is_active=True)
                              .select_related('branch')).order_by('branch__name', 'category', 'name'))
    moves = StockMovement.objects.filter(item__in=[i.id for i in items]).select_related('item', 'animal', 'recorded_by')
    if date_from:
        moves = moves.filter(date__gte=date_from)
    if date_to:
        moves = moves.filter(date__lte=date_to)
    usage = moves.filter(kind='issued').values('item__name', 'item__unit').annotate(used=Sum('quantity')).order_by('item__name')
    return Report(
        title='Stores — Stock & Usage', subtitle=f"{_scope_label(user, branch_name)} · {_period(date_from, date_to)}",
        summary=[('Items', len(items)), ('Low', sum(1 for i in items if i.level == 'low')),
                 ('Out of stock', sum(1 for i in items if i.level == 'out')),
                 ('Movements in period', moves.count())],
        tables=[
            Table('Stock levels', ['Item', 'Category', 'Branch', 'On hand', 'Unit', 'Reorder level', 'Status'],
                  [[i.name, i.get_category_display(), i.branch.name, i.on_hand, i.get_unit_display(), i.reorder_level,
                    i.level_label] for i in items]),
            Table('Usage in period', ['Item', 'Used', 'Unit'],
                  [[u['item__name'], -u['used'], dict(StockItem.UNIT_CHOICES).get(u['item__unit'], '')] for u in usage]),
            Table('Movements', ['Date', 'Item', 'Movement', 'Quantity', 'Animal', 'Batch', 'Expiry', 'Reference', 'By'],
                  [[m.date, m.item.name, m.get_kind_display(), m.quantity, m.animal.name if m.animal else '',
                    m.batch_number, m.expiry_date, m.reference, _name(m.recorded_by)] for m in moves.order_by('date', 'id')]),
        ],
    )


# ------------------------------------------------------------------ Command summary
def command_summary(user, branch_name='', date_from=None, date_to=None, **_):
    from .stock_views import with_on_hand

    rows = []
    for b in _branches(user, branch_name).order_by('name'):
        animals = Animal.objects.filter(branch=b)
        active = animals.filter(status__in=Animal.ACTIVE_STATUSES)
        deps = Deployment.objects.filter(branch=b).exclude(status='cancelled')
        if date_from:
            deps = deps.filter(started_at__date__gte=date_from)
        if date_to:
            deps = deps.filter(started_at__date__lte=date_to)
        completed = deps.filter(status='completed').exclude(outcome='').count()
        positive = deps.filter(outcome='positive').count()
        items = health.schedule(active)
        roster = roster_rows(user, b.name if user.role == 'superadmin' else '')
        stock = list(with_on_hand(StockItem.objects.filter(branch=b, is_active=True)))
        rows.append([
            b.name, active.count(), active.filter(status=Animal.STATUS_OPERATIONAL).count(),
            active.filter(species='dog').count(), active.filter(species='horse').count(),
            deps.count(), f'{round(positive * 100 / completed)}%' if completed else '-',
            DeploymentFind.objects.filter(deployment__in=deps).count(), deps.aggregate(n=Sum('arrests'))['n'] or 0,
            sum(1 for i in items if i.state == 'overdue'),
            sum(1 for r in roster if r['cert_state'] in ('expired', 'missing')),
            HandlerAssignment.objects.filter(animal__in=active, end_date__isnull=True, role='primary').count(),
            sum(1 for i in stock if i.level != 'ok'),
        ])
    totals = ['TOTAL'] + [sum(r[i] for r in rows) if isinstance(rows[0][i], int) else '' for i in range(1, len(rows[0]))] if rows else []
    return Report(
        title='Command Summary', subtitle=f"{_scope_label(user, branch_name)} · deployments {_period(date_from, date_to)}",
        summary=[('Branches', len(rows)), ('Active animals', sum(r[1] for r in rows)),
                 ('Fit for duty', sum(r[2] for r in rows)), ('Deployments', sum(r[5] for r in rows))],
        tables=[Table('By branch', ['Branch', 'Active', 'Fit for duty', 'Dogs', 'Horses', 'Deployments', 'Success',
                                    'Finds', 'Arrests', 'Health overdue', 'Cert issues', 'With handler', 'Stock alerts'],
                      rows + ([totals] if len(rows) > 1 else []))],
    )


# ------------------------------------------------------------------ Single-animal dossier
def animal_dossier(animal):
    cert_rows = [[c.get_cert_type_display(), c.certificate_number, c.issued_date, c.expiry_date, c.state_label]
                 for c in animal.certifications.order_by('-expiry_date')]
    med = MedicalRecord.objects.filter(animal=animal).select_related('veterinarian').order_by('-date_recorded')
    deps = animal.deployment_assignments.select_related('deployment').order_by('-deployment__started_at')
    return Report(
        title=f'Animal Dossier — {animal.name}',
        subtitle=f'{animal.force_number} · {animal.branch.name.title()}',
        summary=[('Status', animal.get_status_display()), ('Specialisation', animal.get_specialisation_display()),
                 ('Deployments', deps.count()), ('Handler', _name(animal.primary_handler) or '-')],
        tables=[
            Table('Profile', ['Field', 'Value'], [
                ['Name', animal.name], ['Force number', animal.force_number], ['Branch', animal.branch.name],
                ['Species', animal.get_species_display()], ['Breed', animal.breed or ''], ['Sex', animal.get_sex_display()],
                ['Date of birth', animal.date_of_birth], ['Colour & markings', animal.colour_markings],
                ['Microchip', animal.microchip_number or ''], ['Brand / tattoo', animal.brand_or_tattoo],
                ['Status', f"{animal.get_status_display()} since {animal.status_since or '-'}"],
                ['Specialisation', animal.get_specialisation_display()],
                ['Sire', animal.sire.name if animal.sire else ''], ['Dam', animal.dam.name if animal.dam else ''],
                ['Acquired', f"{animal.acquisition_date or ''} {animal.get_acquisition_source_display()}".strip()],
                ['Primary handler', _name(animal.primary_handler)],
                ['Housing', animal.current_housing.name if animal.current_housing else ''],
            ]),
            Table('Certificates', ['Certificate', 'Number', 'Issued', 'Expires', 'State'], cert_rows),
            Table('Medical', ['Date', 'Type', 'Diagnosis', 'Treatment', 'Vet'],
                  [[m.date_recorded, m.get_report_type_display(), m.diagnosis, m.treatment, _name(m.veterinarian)] for m in med[:50]]),
            Table('Deployments', ['Reference', 'Date', 'Type', 'Outcome', 'Rating'],
                  [[a.deployment.reference, a.deployment.started_at, a.deployment.get_deployment_type_display(),
                    a.deployment.get_outcome_display(), a.performance or ''] for a in deps[:50]]),
        ],
    )


def _period(date_from, date_to):
    if date_from and date_to:
        return f'{date_from:%d %b %Y} – {date_to:%d %b %Y}'
    if date_from:
        return f'from {date_from:%d %b %Y}'
    if date_to:
        return f'to {date_to:%d %b %Y}'
    return 'all time'


REPORTS = {
    'command': ('Command summary', 'Key figures per branch for command briefings.', command_summary, True),
    'animals': ('Animal register', 'Every animal with status, identification, handler and certificate.', animal_register, False),
    'deployments': ('Deployments & results', 'Call-outs, outcomes, finds and arrests, by type and by animal.', deployments_report, True),
    'compliance': ('Health & certification compliance', 'Overdue treatments, missing records and certificate status.', compliance_report, False),
    'stores': ('Stores — stock & usage', 'Stock levels, usage and every movement in the period.', stores_report, True),
}
