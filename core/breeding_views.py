"""Breeding register: matings, pregnancies, litters/foals and offspring registration."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomUser
from .forms import LitterForm, LitterOutcomeForm, OffspringForm
from .models import Animal, AnimalStatusChange, Litter
from .utils import log_action, notify_users

BREEDING_MANAGERS = ('admin', 'veterinarian', 'superadmin')


def _scoped_litters(user):
    qs = Litter.objects.select_related('dam', 'dam__branch', 'sire')
    return qs if user.role == 'superadmin' else qs.filter(dam__branch=user.branch)


@login_required
def breeding_register(request):
    user = request.user
    branch = None if user.role == 'superadmin' else user.branch
    can_manage = user.role in BREEDING_MANAGERS

    if request.method == 'POST' and can_manage:
        form = LitterForm(request.POST, branch=branch)
        if form.is_valid():
            litter = form.save(commit=False)
            litter.recorded_by = user
            litter.save()
            log_action(user=user, action='create', message=f"Breeding: {litter}")
            messages.success(request, f"Mating recorded — {litter.dam.name} expected "
                                      f"{litter.expected_date:%d %b %Y}." if litter.expected_date else "Mating recorded.")
            return redirect('litter_detail', litter_id=litter.id)
        messages.error(request, 'Please correct the errors in the mating form.')
    else:
        initial = {'dam': request.GET['dam']} if request.GET.get('dam', '').isdigit() else {}
        form = LitterForm(branch=branch, initial=initial)

    litters = _scoped_litters(user)
    open_litters = sorted(litters.filter(status__in=Litter.OPEN_STATUSES),
                          key=lambda l: l.expected_date or timezone.localdate())
    today = timezone.localdate()
    for l in open_litters:
        l.days_to_go = (l.expected_date - today).days if l.expected_date else None
    return render(request, 'core/breeding/register.html', {
        'form': form, 'can_manage': can_manage,
        'open_litters': open_litters,
        'history': litters.exclude(status__in=Litter.OPEN_STATUSES)[:50],
        'stats': {
            'open': len(open_litters),
            'due_soon': sum(1 for l in open_litters if l.days_to_go is not None and l.days_to_go <= 14),
            'born_this_year': litters.filter(status='born', birth_date__year=today.year).count(),
            'offspring': Animal.objects.filter(litter__in=litters).count(),
        },
    })


@login_required
def litter_detail(request, litter_id):
    user = request.user
    litter = get_object_or_404(_scoped_litters(user), pk=litter_id)
    can_manage = user.role in BREEDING_MANAGERS
    outcome_form = LitterOutcomeForm(instance=litter)
    offspring_form = OffspringForm()

    if request.method == 'POST' and can_manage:
        action = request.POST.get('action')
        if action == 'outcome':
            outcome_form = LitterOutcomeForm(request.POST, instance=litter)
            if outcome_form.is_valid():
                litter = outcome_form.save()
                log_action(user=user, action='update', message=f"Breeding outcome: {litter} -> {litter.status}")
                if litter.status == 'born':
                    admins = CustomUser.objects.filter(branch=litter.dam.branch, role__in=('admin', 'veterinarian'), is_active=True)
                    notify_users(users=admins, notification_type='system_alert', title=f'{litter.dam.name} has given birth',
                                 message=f"{litter.born_alive} born alive on {litter.birth_date:%d %b %Y}. Register the offspring.",
                                 link=f'/core/breeding/{litter.id}/')
                messages.success(request, 'Outcome saved.')
                return redirect('litter_detail', litter_id=litter.id)
        elif action == 'offspring' and litter.status == 'born':
            offspring_form = OffspringForm(request.POST)
            if offspring_form.is_valid():
                with transaction.atomic():
                    young = _register_offspring(litter, offspring_form.cleaned_data, user)
                messages.success(request, f"{young.name} registered.")
                return redirect('litter_detail', litter_id=litter.id)
        messages.error(request, 'Please correct the errors below.')

    return render(request, 'core/breeding/litter.html', {
        'litter': litter, 'offspring': litter.offspring.order_by('name'),
        'outcome_form': outcome_form, 'offspring_form': offspring_form, 'can_manage': can_manage,
        'can_register': can_manage and litter.status == 'born',
    })


def _register_offspring(litter, data, user):
    dam = litter.dam
    young = Animal.objects.create(
        name=data['name'], force_number=data['force_number'], sex=data['sex'],
        colour_markings=data.get('colour_markings') or '',
        species=dam.species, breed=dam.breed if (not litter.sire or litter.sire.breed == dam.breed) else '',
        age=0, date_of_birth=litter.birth_date, owner_name='TPF Breeding Programme', branch=dam.branch,
        sire=litter.sire, dam=dam, litter=litter, specialisation='general',
        status='in_training', status_since=litter.birth_date,
        acquisition_date=litter.birth_date, acquisition_source='bred',
        acquired_from=f"Bred in-house: {dam.name} x {litter.sire_name}",
    )
    AnimalStatusChange.objects.create(animal=young, old_status='', new_status='in_training', changed_by=user,
                                      notes=f'Born to {dam.name}')
    log_action(user=user, action='create', message=f"Registered offspring #{young.force_number} {young.name} of {dam.name}")
    return young
