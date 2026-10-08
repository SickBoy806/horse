from django.db import migrations

NOTE = 'Backfilled from assigned users'


def backfill(apps, schema_editor):
    Animal = apps.get_model('core', 'Animal')
    HandlerAssignment = apps.get_model('core', 'HandlerAssignment')
    for animal in Animal.objects.all():
        if HandlerAssignment.objects.filter(animal=animal).exists():
            continue
        handlers = animal.assigned_users.filter(role='user').order_by('id')
        for i, handler in enumerate(handlers):
            HandlerAssignment.objects.create(
                animal=animal, handler=handler, role='primary' if i == 0 else 'secondary',
                start_date=animal.created_at.date(), notes=NOTE,
            )


def undo(apps, schema_editor):
    apps.get_model('core', 'HandlerAssignment').objects.filter(notes=NOTE).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0026_handler_teams_certifications')]
    operations = [migrations.RunPython(backfill, undo)]
