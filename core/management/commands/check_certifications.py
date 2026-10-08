"""Notify branch admins and handlers about certificates that are expiring or have expired.

Run daily (Windows Task Scheduler / cron):
    python manage.py check_certifications

Each certificate is notified at most once per threshold ('expiring', then 'expired'), so the job
is safe to run as often as you like. Renewed (superseded) certificates and animals that have left
service are ignored.
"""
from django.core.management.base import BaseCommand

from accounts.models import CustomUser
from core.models import Animal, Certification
from core.utils import notify_users


class Command(BaseCommand):
    help = 'Send expiry reminders for current animal/team certifications.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='List what would be sent without notifying.')

    def handle(self, *args, dry_run=False, **options):
        current = Certification.current(
            Certification.objects.filter(animal__status__in=Animal.ACTIVE_STATUSES)
        ).select_related('animal__branch', 'handler')

        sent = 0
        for cert in current:
            state = cert.state
            if state == 'valid' or cert.reminder_sent == state:
                continue
            animal = cert.animal
            if state == 'expired':
                title = 'Certificate expired'
                message = (f"{animal.name} ({animal.force_number}): {cert.get_cert_type_display()} "
                           f"expired on {cert.expiry_date:%d %b %Y}.")
            else:
                title = 'Certificate expiring soon'
                message = (f"{animal.name} ({animal.force_number}): {cert.get_cert_type_display()} "
                           f"expires in {cert.days_left} days ({cert.expiry_date:%d %b %Y}).")

            recipients = set(CustomUser.objects.filter(branch=animal.branch, role='admin', is_active=True))
            if cert.handler:
                recipients.add(cert.handler)
            if animal.primary_handler:
                recipients.add(animal.primary_handler)

            self.stdout.write(f"[{state}] {message} -> {', '.join(sorted(u.username for u in recipients)) or 'nobody'}")
            sent += 1
            if dry_run:
                continue
            notify_users(users=recipients, notification_type='system_alert', title=title, message=message,
                         link=f'/core/animals/{animal.id}/#certifications')
            cert.reminder_sent = state
            cert.save(update_fields=['reminder_sent'])

        verb = 'Would send' if dry_run else 'Sent'
        self.stdout.write(self.style.SUCCESS(f"{verb} reminders for {sent} certificate(s)." if sent else 'No reminders due.'))
