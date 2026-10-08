import uuid

from django.db import migrations, models


def give_each_animal_a_token(apps, schema_editor):
    Animal = apps.get_model('core', 'Animal')
    for animal in Animal.objects.filter(card_token__isnull=True):
        animal.card_token = uuid.uuid4()
        animal.save(update_fields=['card_token'])


class Migration(migrations.Migration):
    # Three steps so existing rows each get their own token (a plain default would give them all the same one).
    dependencies = [('core', '0032_transfers_breeding')]

    operations = [
        migrations.AddField('animal', 'card_token', models.UUIDField(null=True, editable=False)),
        migrations.AddField('animal', 'card_issued', models.DateField(null=True, blank=True, editable=False)),
        migrations.RunPython(give_each_animal_a_token, migrations.RunPython.noop),
        migrations.AlterField('animal', 'card_token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
    ]
