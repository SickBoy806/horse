import csv
from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomUser
from .forms import DeploymentFindFormSet, DeploymentForm, DeploymentTeamFormSet
from .models import Animal, Branch, Deployment, DeploymentFind, HandlerAssignment
from .utils import log_action, notify_users


def _scoped(user):
    """Deployments the user may see: every branch for superadmins, otherwise their own."""
    qs = Deployment.objects.select_related('branch', 'created_by')
    if user.role == 'superadmin':
        return qs
    return qs.filter(branch=user.branch)


def _can_edit(user, deployment):
    if user.role == 'superadmin':
        return True
    if deployment.branch_id != getattr(user.branch, 'id', None):
        return False
    return user.role == 'admin' or deployment.created_by_id == user.id


def _parse_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _summary(qs):
    agg = qs.aggregate(arrests=Sum('arrests'), persons=Sum('persons_located'))
    completed_with_outcome = qs.filter(status='completed').exclude(outcome='').count()
    positive = qs.filter(outcome='positive').count()
    rate = round(positive * 100 / completed_with_outcome) if completed_with_outcome else None
    return {
        'success_label': f'{rate}%' if rate is not None else '—',
        'total': qs.count(),
        'in_progress': qs.filter(status='in_progress').count(),
        'positive': positive,
        'success_rate': rate,
        'arrests': agg['arrests'] or 0,
        'persons': agg['persons'] or 0,
        'finds': DeploymentFind.objects.filter(deployment__in=qs).count(),
    }


@login_required
def deployment_list(request):
    user = request.user
    deployments = _scoped(user)

    f = {k: request.GET.get(k, '').strip() for k in
         ('q', 'type', 'status', 'outcome', 'branch', 'animal', 'date_from', 'date_to')}
    if f['q']:
        deployments = deployments.filter(
            Q(reference__icontains=f['q']) | Q(location__icontains=f['q']) |
            Q(ob_number__icontains=f['q']) | Q(requested_by__icontains=f['q'])
        )
    if f['type']:
        deployments = deployments.filter(deployment_type=f['type'])
    if f['status']:
        deployments = deployments.filter(status=f['status'])
    if f['outcome']:
        deployments = deployments.filter(outcome=f['outcome'])
    if f['branch'] and user.role == 'superadmin':
        deployments = deployments.filter(branch__name=f['branch'])
    if f['animal'].isdigit():
        deployments = deployments.filter(animals__id=int(f['animal']))
    tz = timezone.get_current_timezone()
    date_from, date_to = _parse_date(f['date_from']), _parse_date(f['date_to'])
    if date_from:
        deployments = deployments.filter(started_at__gte=datetime.combine(date_from, time.min, tzinfo=tz))
    if date_to:
        deployments = deployments.filter(started_at__lte=datetime.combine(date_to, time.max, tzinfo=tz))
    deployments = deployments.distinct()

    if request.GET.get('export') == 'csv':
        return _export_csv(deployments)

    page_obj = Paginator(
        deployments.annotate(n_animals=Count('team', distinct=True), n_finds=Count('finds', distinct=True))
                   .order_by('-started_at', '-id'),
        20,
    ).get_page(request.GET.get('page'))

    animal_choices = Animal.objects.all() if user.role == 'superadmin' else Animal.objects.filter(branch=user.branch)
    query = request.GET.copy()
    query.pop('page', None)
    query.pop('export', None)

    return render(request, 'core/deployments/list.html', {
        'page_obj': page_obj,
        'stats': _summary(deployments),
        'f': f,
        'querystring': query.urlencode(),
        'type_choices': Deployment.TYPE_CHOICES,
        'status_choices': Deployment.STATUS_CHOICES,
        'outcome_choices': Deployment.OUTCOME_CHOICES,
        'animal_choices': animal_choices.order_by('name'),
        'branches': Branch.objects.filter(is_active=True).order_by('name') if user.role == 'superadmin' else None,
    })


def _export_csv(deployments):
    stamp = timezone.localtime().strftime('%Y%m%d-%H%M')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="deployments-{stamp}.csv"'
    response.write('﻿')  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(response)
    writer.writerow(['Reference', 'Started', 'Ended', 'Branch', 'Type', 'Location', 'OB / Case No.',
                     'Requested by', 'Status', 'Outcome', 'Animals', 'Handlers', 'Finds',
                     'Arrests', 'Persons located', 'Logged by'])
    deployments = deployments.prefetch_related('team__animal', 'team__handler', 'finds')
    for d in deployments:
        team = list(d.team.all())
        writer.writerow([
            d.reference,
            timezone.localtime(d.started_at).strftime('%Y-%m-%d %H:%M'),
            timezone.localtime(d.ended_at).strftime('%Y-%m-%d %H:%M') if d.ended_at else '',
            d.branch.name, d.get_deployment_type_display(), d.location, d.ob_number, d.requested_by,
            d.get_status_display(), d.get_outcome_display(),
            '; '.join(f'{t.animal.name} ({t.animal.force_number})' for t in team),
            '; '.join(t.handler.get_full_name() or t.handler.username for t in team if t.handler),
            '; '.join(
                f'{x.get_find_type_display()}'
                + (f' {x.quantity.normalize():f} {x.get_unit_display()}' if x.quantity is not None else '')
                + (f' — {x.description}' if x.description else '')
                for x in d.finds.all()
            ),
            d.arrests, d.persons_located,
            (d.created_by.get_full_name() or d.created_by.username) if d.created_by else '',
        ])
    return response


@login_required
def deployment_detail(request, deployment_id):
    deployment = get_object_or_404(_scoped(request.user), pk=deployment_id)
    return render(request, 'core/deployments/detail.html', {
        'deployment': deployment,
        'team': deployment.team.select_related('animal', 'handler'),
        'finds': deployment.finds.select_related('indicated_by'),
        'can_edit': _can_edit(request.user, deployment),
    })


@login_required
def deployment_form(request, deployment_id=None):
    user = request.user
    if deployment_id:
        deployment = get_object_or_404(_scoped(user), pk=deployment_id)
        if not _can_edit(user, deployment):
            return render(request, 'errors/unauthorized.html', status=403)
    else:
        if not user.branch and user.role != 'superadmin':
            return render(request, 'errors/branch_not_found.html', status=403)
        deployment = Deployment(branch=user.branch, created_by=user, started_at=timezone.now())

    # Animals/handlers offered in the team rows come from the deployment's branch.
    branch = deployment.branch if deployment.pk else user.branch
    if user.role == 'superadmin':
        posted = request.POST.get('branch') if request.method == 'POST' else None
        branch = Branch.objects.filter(pk=posted).first() if posted else (deployment.branch if deployment.pk else None)

    is_new = deployment.pk is None
    if request.method == 'POST':
        form = DeploymentForm(request.POST, instance=deployment, user=user)
        team_fs = DeploymentTeamFormSet(request.POST, instance=deployment, prefix='team', form_kwargs={'branch': branch})
        finds_fs = DeploymentFindFormSet(request.POST, instance=deployment, prefix='finds', form_kwargs={'branch': branch})
        if form.is_valid() and team_fs.is_valid() and finds_fs.is_valid():
            target_branch = form.cleaned_data.get('branch') or deployment.branch
            wrong = [f.cleaned_data['animal'].name for f in team_fs.forms
                     if f.cleaned_data and not f.cleaned_data.get('DELETE')
                     and f.cleaned_data.get('animal') and f.cleaned_data['animal'].branch_id != target_branch.id]
            if wrong:
                form.add_error(None, f"Not in {target_branch.name}: {', '.join(wrong)}.")
            else:
                with transaction.atomic():
                    deployment = form.save()
                    team_fs.instance = finds_fs.instance = deployment
                    team_fs.save()
                    finds_fs.save()
                _after_save(request, deployment, is_new)
                return redirect('deployment_detail', deployment_id=deployment.id)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DeploymentForm(instance=deployment, user=user)
        team_fs = DeploymentTeamFormSet(instance=deployment, prefix='team', form_kwargs={'branch': branch})
        finds_fs = DeploymentFindFormSet(instance=deployment, prefix='finds', form_kwargs={'branch': branch})

    primaries = HandlerAssignment.objects.filter(role='primary', end_date__isnull=True)
    if branch is not None:
        primaries = primaries.filter(animal__branch=branch)
    return render(request, 'core/deployments/form.html', {
        'form': form, 'team_fs': team_fs, 'finds_fs': finds_fs,
        'deployment': deployment, 'is_new': is_new,
        # animal id -> primary handler id, used to pre-fill the handler when an animal is picked
        'primary_handlers': {str(a): h for a, h in primaries.values_list('animal_id', 'handler_id')},
    })


def _after_save(request, deployment, is_new):
    user = request.user
    verb = 'Logged' if is_new else 'Updated'
    log_action(user=user, action='create' if is_new else 'update',
               message=f"{verb} deployment {deployment.reference} ({deployment.get_deployment_type_display()})")
    messages.success(request, f"{verb} deployment {deployment.reference}.")
    if is_new:
        admins = CustomUser.objects.filter(branch=deployment.branch, role='admin').exclude(pk=user.pk)
        notify_users(
            users=admins,
            notification_type='system_alert',
            title='New deployment logged',
            message=f"{deployment.reference}: {deployment.get_deployment_type_display()} at {deployment.location}",
            link=f'/core/deployments/{deployment.id}/',
        )
