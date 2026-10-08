"""Stores reminders: low / out-of-stock items and batches nearing expiry.

    python manage.py check_stock [--dry-run]

Low stock is also flagged the moment a movement crosses the reorder level; this sweep catches items whose
reorder level was raised and notifies each expiring batch once.
"""
from django.core.management.base import BaseCommand

from accounts.models import CustomUser
from core.models import StockItem, StockMovement
from core.stock_views import check_level
from core.utils import notify_users


class Command(BaseCommand):
    help = 'Send stores reminders (low stock, expiring batches).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, dry_run=False, **options):
        sent = 0
        for item in StockItem.objects.filter(is_active=True).select_related('branch'):
            if not dry_run:
                was = item.low_stock_notified
                check_level(item)
                if not was and StockItem.objects.get(pk=item.pk).low_stock_notified:
                    sent += 1
                    self.stdout.write(f"[low] {item.name} ({item.branch.name})")
            batches = item.expiring_batches().filter(expiry_notified=False)
            for batch in batches:
                label = 'expired' if batch.is_expired else 'expiring'
                message = (f"{item.name}: batch {batch.batch_number or batch.date} {label} "
                           f"{batch.expiry_date:%d %b %Y}. Check the shelf and write off expired stock.")
                self.stdout.write(f"[{label}] {message}")
                sent += 1
                if dry_run:
                    continue
                roles = ('admin', 'staff', 'veterinarian') if item.category in StockItem.MEDICAL_CATEGORIES else ('admin', 'staff')
                notify_users(users=CustomUser.objects.filter(branch=item.branch, role__in=roles, is_active=True),
                             notification_type='system_alert', title=f'Stock batch {label}: {item.name}',
                             message=message, link=f'/core/stock/{item.id}/')
                StockMovement.objects.filter(pk=batch.pk).update(expiry_notified=True)
        verb = 'Would send' if dry_run else 'Sent'
        self.stdout.write(self.style.SUCCESS(f"{verb} {sent} stores reminder(s)." if sent else 'No stores reminders due.'))
