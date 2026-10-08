from datetime import timedelta

from django import template
from django.db.models import Count, Q, Sum
from django.utils import timezone

from core.health import missing_records, schedule, scoped_animals
from core.models import Animal, Deployment, DeploymentFind

register = template.Library()


@register.inclusion_tag('partials/readiness_panel.html', takes_context=True)
def readiness_panel(context):
    """Fit-for-duty overview for the viewer's branch (all branches for superadmins)."""
    user = context['request'].user
    animals = Animal.objects.all()
    if getattr(user, 'role', None) != 'superadmin':
        animals = animals.filter(branch=user.branch)

    by_status = dict(animals.values_list('status').annotate(n=Count('id')))
    fit_by_species = dict(
        animals.filter(status=Animal.STATUS_OPERATIONAL).values_list('species').annotate(n=Count('id'))
    )
    active_by_species = dict(
        animals.filter(status__in=Animal.ACTIVE_STATUSES).values_list('species').annotate(n=Count('id'))
    )

    fit = by_status.get(Animal.STATUS_OPERATIONAL, 0)
    active = sum(by_status.get(s, 0) for s in Animal.ACTIVE_STATUSES)
    rows = [
        {'value': value, 'label': label, 'count': by_status.get(value, 0),
         'badge': Animal(status=value).status_badge}
        for value, label in Animal.STATUS_CHOICES
    ]

    return {
        'fit': fit,
        'active': active,
        'readiness_pct': round(fit * 100 / active) if active else 0,
        'dogs_fit': fit_by_species.get('dog', 0),
        'dogs_active': active_by_species.get('dog', 0),
        'horses_fit': fit_by_species.get('horse', 0),
        'horses_active': active_by_species.get('horse', 0),
        'rows': rows,
        'all_branches': getattr(user, 'role', None) == 'superadmin',
    }


@register.inclusion_tag('partials/operations_panel.html', takes_context=True)
def operations_panel(context, days=30):
    """Last-N-days deployment results, live operations and top performers."""
    user = context['request'].user
    deployments = Deployment.objects.exclude(status='cancelled')
    animals = Animal.objects.all()
    if getattr(user, 'role', None) != 'superadmin':
        deployments = deployments.filter(branch=user.branch)
        animals = animals.filter(branch=user.branch)

    recent = deployments.filter(started_at__gte=timezone.now() - timedelta(days=days))
    completed = recent.filter(status='completed').exclude(outcome='').count()
    positive = recent.filter(outcome='positive').count()

    top = (animals
           .annotate(positive=Count('deployment_assignments', filter=Q(
               deployment_assignments__deployment__outcome='positive',
               deployment_assignments__deployment__in=recent)))
           .filter(positive__gt=0).order_by('-positive', 'name')[:3])

    return {
        'days': days,
        'count': recent.count(),
        'success_rate': f'{round(positive * 100 / completed)}%' if completed else '—',
        'finds': DeploymentFind.objects.filter(deployment__in=recent).count(),
        'arrests': recent.aggregate(n=Sum('arrests'))['n'] or 0,
        'live': deployments.filter(status='in_progress').select_related('branch').order_by('-started_at')[:4],
        'top': top,
        'all_branches': getattr(user, 'role', None) == 'superadmin',
    }


@register.inclusion_tag('partials/cert_alerts_panel.html', takes_context=True)
def cert_alerts_panel(context, limit=5):
    """Teams needing attention: expired / expiring / missing role certificates and animals without a handler."""
    from core.team_views import roster_rows  # local import: team_views pulls in forms

    rows = roster_rows(context['request'].user)
    urgency = {'expired': 0, 'missing': 1, 'expiring': 2}
    issues = sorted(
        (r for r in rows if r['cert_state'] in urgency),
        key=lambda r: (urgency[r['cert_state']], r['role_cert'].expiry_date if r['role_cert'] else timezone.localdate()),
    )
    return {
        'issues': issues[:limit],
        'more': max(len(issues) - limit, 0),
        'counts': {k: sum(1 for r in rows if r['cert_state'] == k) for k in ('expired', 'expiring', 'missing')},
        'no_handler': sum(1 for r in rows if not r['primary']),
        'total': len(rows),
    }


@register.inclusion_tag('partials/health_alerts_panel.html', takes_context=True)
def health_alerts_panel(context, limit=6):
    """Overdue / due-soon vaccinations and deworming for the viewer's animals."""
    user = context['request'].user
    animals = scoped_animals(user)
    items = schedule(animals)
    urgent = [i for i in items if i.state in ('overdue', 'due_soon')]
    return {
        'urgent': urgent[:limit],
        'more': max(len(urgent) - limit, 0),
        'overdue': sum(1 for i in urgent if i.state == 'overdue'),
        'due_soon': sum(1 for i in urgent if i.state == 'due_soon'),
        'missing': len(missing_records(list(animals))),
        'next_item': next((i for i in items if i.state == 'upcoming'), None),
        'can_record': getattr(user, 'role', None) == 'veterinarian' and user.branch is not None,
        'request': context['request'],
    }


@register.inclusion_tag('partials/stock_alerts_panel.html', takes_context=True)
def stock_alerts_panel(context, limit=6):
    """Low / out-of-stock items and batches nearing expiry for the viewer's stores."""
    from core.stock_views import _scoped_items, with_on_hand  # local: stock_views imports forms

    items = [i for i in with_on_hand(_scoped_items(context['request'].user).filter(is_active=True))]
    problems = sorted((i for i in items if i.level != 'ok'), key=lambda i: (i.level != 'out', i.name))
    expiring = [i for i in items if i.expiring_batches().exists()]
    return {'problems': problems[:limit], 'more': max(len(problems) - limit, 0),
            'out': sum(1 for i in items if i.level == 'out'), 'low': sum(1 for i in items if i.level == 'low'),
            'expiring': expiring[:3], 'expiring_count': len(expiring), 'total': len(items)}
