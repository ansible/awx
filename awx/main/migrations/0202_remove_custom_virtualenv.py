# -*- coding: utf-8 -*-
# Generated for custom venv removal

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0201_squashed_deletions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventorysource',
            name='custom_virtualenv',
        ),
        migrations.RemoveField(
            model_name='inventoryupdate',
            name='custom_virtualenv',
        ),
        migrations.RemoveField(
            model_name='job',
            name='custom_virtualenv',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='custom_virtualenv',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='custom_virtualenv',
        ),
        migrations.RemoveField(
            model_name='project',
            name='custom_virtualenv',
        ),
    ]
