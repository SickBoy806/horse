"""Remind vets, branch admins and handlers about vaccinations, deworming and farrier visits due soon or overdue.

    python manage.py check_health_due [--dry-run]

Each dose is notified at most once per state ('due_soon', then 'overdue'); recording the next dose
supersedes the old one, so its reminders stop automatically.
"""
from django.core.management.base import BaseCommand

from accounts.models import CustomUser
from core.health import schedule
from core.models import Animal, HealthReminderLog
from core.utils import notify_users


class Command(BaseCommand):
    help = 'Send due / overdue reminders for vaccinations, deworming and farrier visits.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='List what would be sent without notifying.')

    def handle(self, *args, dry_run=False, **options):
        animals = Animal.objects.filter(status__in=Animal.ACTIVE_STATUSES)
        already = set()
        for rec, hoof, litter, state in HealthReminderLog.objects.values_list('record_id', 'hoof_record_id', 'litter_id', 'state'):
            already.add(('birth', litter, state) if litter else ('farrier', hoof, state) if hoof else ('medical', rec, state))

        sent = 0
        for item in schedule(animals):
            series = 'birth' if item.is_birth else 'farrier' if item.is_farrier else 'medical'
            if item.state == 'upcoming' or (series, item.record.id, item.state) in already:
                continue
            animal = item.animal
            if item.is_birth and item.state == 'overdue':
                title = 'Birth overdue - record the outcome'
                message = (f"{animal.name} ({animal.force_number}) was due to give birth {item.due_date:%d %b %Y} "
                           f"({item.days_late} day(s) ago). Record the outcome in the breeding register.")
            elif item.state == 'overdue':
                title = f'{item.kind_label} overdue'
                message = (f"{animal.name} ({animal.force_number}): {item.label} was due "
                           f"{item.due_date:%d %b %Y} — {item.days_late} day(s) overdue.")
            else:
                title = f'{item.kind_label} due soon'
                when = 'today' if item.days == 0 else f'in {item.days} day(s)'
                message = f"{animal.name} ({animal.force_number}): {item.label} due {when} ({item.due_date:%d %b %Y})."

            recipients = set(CustomUser.objects.filter(
                branch=animal.branch, role__in=('admin', 'veterinarian'), is_active=True))
            if animal.assigned_vet:
                recipients.add(animal.assigned_vet)
            if animal.primary_handler:
                recipients.add(animal.primary_handler)

            self.stdout.write(f"[{item.state}] {message} -> {', '.join(sorted(u.username for u in recipients)) or 'nobody'}")
            sent += 1
            if dry_run:
                continue
            notify_users(users=recipients, notification_type='system_alert', title=title, message=message,
                         link=f'/core/animals/{animal.id}/')
            if item.is_birth:
                HealthReminderLog.objects.create(litter=item.record, state=item.state)
            elif item.is_farrier:
                HealthReminderLog.objects.create(hoof_record=item.record, state=item.state)
            else:
                HealthReminderLog.objects.create(record=item.record, state=item.state)

        verb = 'Would send' if dry_run else 'Sent'
        self.stdout.write(self.style.SUCCESS(f"{verb} {sent} health reminder(s)." if sent else 'No health reminders due.'))
