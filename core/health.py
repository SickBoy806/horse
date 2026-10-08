"""Preventive-care schedule: vaccinations and deworming (from vet medical records) and farrier visits.

The latest dose per (animal, vaccine), the latest deworming per animal and the latest farrier visit per
horse define what is due: recording the next one supersedes the old due date, so the alert clears.
"""
from dataclasses import dataclass
from datetime import date

from django.utils import timezone

from .models import Animal, HoofCareRecord, Litter, MedicalRecord

DUE_SOON_DAYS = 14
KINDS = {'vaccination': 'Vaccination', 'deworming': 'Deworming', 'farrier': 'Farrier', 'birth': 'Expected birth'}
RECORDABLE_KINDS = ('vaccination', 'deworming', 'farrier')  # kinds that can be 'never recorded'
MEDICAL_KINDS = ('vaccination', 'deworming')


@dataclass
class HealthItem:
    animal: Animal
    kind: str               # 'vaccination' | 'deworming' | 'farrier'
    label: str              # vaccine / dewormer name, or farrier service
    due_date: date
    last_given: date
    record: object          # MedicalRecord, HoofCareRecord or Litter
    by: str = ''            # vet or farrier who did the last one

    @property
    def days(self):
        return (self.due_date - timezone.localdate()).days

    @property
    def days_late(self):
        return max(-self.days, 0)

    @property
    def state(self):
        if self.days < 0:
            return 'overdue'
        if self.days <= DUE_SOON_DAYS:
            return 'due_soon'
        return 'upcoming'

    @property
    def state_label(self):
        return {'overdue': 'Overdue', 'due_soon': 'Due soon', 'upcoming': 'Upcoming'}[self.state]

    @property
    def badge(self):
        return {'overdue': 'tpf-badge-red', 'due_soon': 'tpf-badge-amber', 'upcoming': 'tpf-badge-green'}[self.state]

    @property
    def kind_label(self):
        return KINDS[self.kind]

    @property
    def is_farrier(self):
        return self.kind == 'farrier'

    @property
    def is_birth(self):
        return self.kind == 'birth'


def _key_and_due(record):
    if record.report_type == 'vaccination':
        name = (record.vaccine_name or '').strip()
        return (record.animal_id, 'vaccination', name.lower()), record.next_due_date, name or 'Vaccination'
    name = (record.dewormer_name or '').strip()
    return (record.animal_id, 'deworming', ''), record.next_deworming_date, name or 'Deworming'


def _user_name(user):
    return (user.get_full_name() or user.username) if user else ''


def schedule(animals):
    """Due items for the given animals, soonest first. Only the latest record of each series counts."""
    latest = {}
    records = (MedicalRecord.objects
               .filter(animal__in=animals, report_type__in=MEDICAL_KINDS)
               .select_related('animal', 'animal__branch', 'veterinarian')
               .order_by('date_recorded', 'id'))
    for record in records:
        key, due, label = _key_and_due(record)
        latest[key] = HealthItem(animal=record.animal, kind=key[1], label=label, due_date=due,
                                 last_given=timezone.localtime(record.date_recorded).date(), record=record,
                                 by=_user_name(record.veterinarian))

    visits = (HoofCareRecord.objects.filter(animal__in=animals)
              .select_related('animal', 'animal__branch').order_by('date', 'id'))
    for visit in visits:
        latest[(visit.animal_id, 'farrier', '')] = HealthItem(
            animal=visit.animal, kind='farrier', label=visit.get_service_display(), due_date=visit.next_due,
            last_given=visit.date, record=visit, by=visit.farrier)

    litters = (Litter.objects.filter(dam__in=animals, status__in=Litter.OPEN_STATUSES, expected_date__isnull=False)
               .select_related('dam', 'dam__branch', 'sire'))
    for litter in litters:
        label = 'Expected foaling' if litter.dam.species == 'horse' else 'Expected whelping'
        latest[(litter.dam_id, 'birth', litter.id)] = HealthItem(
            animal=litter.dam, kind='birth', label=label, due_date=litter.expected_date,
            last_given=litter.mating_date, record=litter, by=f'Sire: {litter.sire_name}')

    # A latest record without a next date means the course / cycle is finished.
    items = [item for item in latest.values() if item.due_date]
    return sorted(items, key=lambda i: (i.due_date, i.animal.name))


def missing_records(animals):
    """(animal, kind) pairs for active animals with no record yet (farrier applies to horses only)."""
    have = set(MedicalRecord.objects.filter(animal__in=animals, report_type__in=MEDICAL_KINDS)
               .values_list('animal_id', 'report_type').distinct())
    have |= {(a, 'farrier') for a in HoofCareRecord.objects.filter(animal__in=animals)
             .values_list('animal_id', flat=True).distinct()}
    missing = []
    for a in animals:
        for kind in RECORDABLE_KINDS:
            if kind == 'farrier' and a.species != 'horse':
                continue
            if (a.id, kind) not in have:
                missing.append((a, kind))
    return missing


def scoped_animals(user):
    """Active animals the user is responsible for seeing."""
    animals = Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES).select_related('branch')
    if getattr(user, 'role', None) != 'superadmin':
        animals = animals.filter(branch=user.branch)
    return animals.order_by('name')


def animal_overdue(animal):
    """True when any preventive treatment for this animal is overdue (used for deployment warnings)."""
    return any(i.state == 'overdue' for i in schedule(Animal.objects.filter(pk=animal.pk)))
