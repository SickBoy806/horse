"""Run every daily reminder job — the one command to schedule (Task Scheduler / cron):

    python manage.py run_daily_reminders
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run all daily reminder jobs (certificate expiry, health/farrier due, stores).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, dry_run=False, **options):
        for job in ('check_certifications', 'check_health_due', 'check_stock'):
            self.stdout.write(self.style.MIGRATE_HEADING(f'== {job}'))
            call_command(job, dry_run=dry_run, stdout=self.stdout, stderr=self.stderr)
