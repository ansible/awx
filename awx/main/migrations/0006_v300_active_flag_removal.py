# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from awx.main.migrations import _cleanup_deleted as cleanup_deleted
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_v300_migrate_facts'),
    ]

    operations = [
        migrations.RunPython(cleanup_deleted.cleanup_deleted),

        migrations.RemoveField(
            model_name='credential',
            name='active',
        ),
        migrations.RemoveField(
            model_name='custominventoryscript',
            name='active',
        ),
        migrations.RemoveField(
            model_name='group',
            name='active',
        ),
        migrations.RemoveField(
            model_name='host',
            name='active',
        ),
        migrations.RemoveField(
            model_name='inventory',
            name='active',
        ),
        migrations.RemoveField(
            model_name='notifier',
            name='active',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='active',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='active',
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='active',
        ),
        migrations.RemoveField(
            model_name='team',
            name='active',
        ),
        migrations.RemoveField(
            model_name='unifiedjob',
            name='active',
        ),
        migrations.RemoveField(
            model_name='unifiedjobtemplate',
            name='active',
        ),
    ]
