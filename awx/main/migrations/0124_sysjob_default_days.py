# -*- coding: utf-8 -*-

from django.db import migrations, models

from awx.main.utils.common import set_current_apps
from awx.main.models import SystemJobTemplate


def set_default_days(apps, schema_editor):
    set_current_apps(apps)
    for sys_template in SystemJobTemplate.objects.all():
        if sys_template.has_configurable_retention:
            if sys_template.default_days is None:
                sys_template.default_days = 30
                sys_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0123_drop_hg_support'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemjob',
            name='default_days',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='systemjobtemplate',
            name='default_days',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.RunPython(set_default_days),
    ]
