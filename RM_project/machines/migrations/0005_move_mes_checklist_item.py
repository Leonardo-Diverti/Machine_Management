from django.db import migrations


def move_mes_to_it(apps, schema_editor):
    MachineChecklistItem = apps.get_model('machines', 'MachineChecklistItem')

    MachineChecklistItem.objects.filter(codice='allacciamento_mes').update(
        ufficio='IT',
        solo_visualizzazione_tech=False,
    )
    MachineChecklistItem.objects.filter(codice='collegamento_niagara').delete()


def reverse_move_mes_to_tech(apps, schema_editor):
    MachineChecklistItem = apps.get_model('machines', 'MachineChecklistItem')

    MachineChecklistItem.objects.filter(codice='allacciamento_mes').update(
        ufficio='TECH',
        solo_visualizzazione_tech=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('machines', '0004_machine_tipo_macchina_alter_machine_stato_and_more'),
    ]

    operations = [
        migrations.RunPython(move_mes_to_it, reverse_move_mes_to_tech),
    ]